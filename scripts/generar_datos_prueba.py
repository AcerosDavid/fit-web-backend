#!/usr/bin/env python
"""
Exporta los datos de prueba (generados por los seeders) a un archivo Excel.

Uso (desde la raíz del proyecto, con datos ya sembrados):
    python scripts/generar_datos_prueba.py [ruta_salida]

Salida por defecto:
    complementos/datos_prueba.xlsx

Los datos se obtienen con los managers de Django: por ejemplo, en Clientes
solo se exportan los registros vivos (SoftDeleteManager), y en Asistencias se
muestra la duración calculada de cada visita.
"""
import os
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import django

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django.setup()

from openpyxl import Workbook  # noqa: E402
from openpyxl.styles import Alignment, Font, PatternFill  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402

from attendance.models import Attendance  # noqa: E402
from coaches.models import Coach, CoachAttendance  # noqa: E402
from members.models import Member  # noqa: E402
from memberships.models import Membership  # noqa: E402
from payments.models import Payment  # noqa: E402
from plans.models import Plan  # noqa: E402
from users.models import User  # noqa: E402

ENCABEZADO = PatternFill("solid", fgColor="1F4E79")
ENCABEZADO_LETRA = Font(color="FFFFFF", bold=True)


def texto(valor):
    """Convierte un valor de modelo a texto plano apto para Excel."""
    if valor is None:
        return ""
    if isinstance(valor, datetime):
        return valor.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(valor, date):
        return valor.strftime("%Y-%m-%d")
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, bool):
        return "Sí" if valor else "No"
    return str(valor) if not isinstance(valor, (int, float)) else valor


def agregar_hoja(wb, titulo, encabezados, filas):
    ws = wb.create_sheet(titulo)
    ws.append(encabezados)
    for fila in filas:
        ws.append([texto(valor) for valor in fila])

    for cell in ws[1]:
        cell.fill = ENCABEZADO
        cell.font = ENCABEZADO_LETRA
        cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    for columna in ws.columns:
        ancho = max(len(str(c.value)) if c.value is not None else 0 for c in columna)
        ws.column_dimensions[get_column_letter(columna[0].column)].width = min(max(ancho + 2, 12), 45)
    return ws


def construir_libro() -> Workbook:
    wb = Workbook()
    wb.remove(wb.active)

    # ── Resumen ─────────────────────────────────────────────────────────────
    resumen = [
        ("Usuarios (staff)", User.objects.count()),
        ("Clientes activos", Member.objects.count()),
        ("Clientes eliminados (soft-delete)", Member.all_objects.filter(deleted_at__isnull=False).count()),
        ("Planes", Plan.objects.count()),
        ("Membresías", Membership.objects.count()),
        ("Pagos", Payment.objects.count()),
        ("Asistencias de clientes", Attendance.objects.count()),
        ("Entrenadores", Coach.objects.count()),
        ("Asistencias de entrenadores", CoachAttendance.objects.count()),
    ]
    agregar_hoja(wb, "Resumen", ["Conjunto de datos", "Registros"], resumen)

    # ── Usuarios ────────────────────────────────────────────────────────────
    agregar_hoja(
        wb,
        "Usuarios",
        ["ID", "Usuario", "Correo", "Nombre", "Apellido", "Rol", "Es staff", "Último acceso", "Activo"],
        [
            (
                u.id,
                u.username,
                u.email,
                u.first_name,
                u.last_name,
                u.get_role_display(),
                u.is_staff,
                u.last_login,
                u.is_active,
            )
            for u in User.objects.all().order_by("id")
        ],
    )

    # ── Clientes ─────────────────────────────────────────────────────────────
    agregar_hoja(
        wb,
        "Clientes",
        ["ID", "Nombre", "Apellido", "Correo", "Teléfono", "Nacimiento", "Género", "Estado", "QR", "Creado"],
        [
            (
                m.id,
                m.first_name,
                m.last_name,
                m.email,
                m.phone,
                m.date_of_birth,
                m.get_gender_display(),
                m.get_status_display(),
                m.qr_code,
                m.created_at,
            )
            for m in Member.objects.all()
        ],
    )

    # ── Planes ──────────────────────────────────────────────────────────────
    agregar_hoja(
        wb,
        "Planes",
        ["ID", "Nombre", "Descripción", "Precio", "Duración (días)", "Activo", "Membresías"],
        [
            (
                p.id,
                p.name,
                p.description,
                p.price,
                p.duration_days,
                p.is_active,
                p.memberships.count(),
            )
            for p in Plan.objects.all()
        ],
    )

    # ── Membresías ──────────────────────────────────────────────────────────
    agregar_hoja(
        wb,
        "Membresías",
        ["ID", "Cliente", "Plan", "Inicio", "Fin", "Estado", "Válida hoy", "Creada por", "Total pagado"],
        [
            (
                me.id,
                me.member.full_name,
                me.plan.name,
                me.start_date,
                me.end_date,
                me.get_status_display(),
                me.is_valid,
                me.created_by.username if me.created_by else "",
                float(sum((p.amount for p in me.payments.all()), Decimal("0"))),
            )
            for me in Membership.objects.select_related("member", "plan", "created_by")
        ],
    )

    # ── Pagos ───────────────────────────────────────────────────────────────
    agregar_hoja(
        wb,
        "Pagos",
        ["ID", "Cliente", "Membresía", "Monto", "Método", "Fecha", "Recibido por", "Notas"],
        [
            (
                p.id,
                p.membership.member.full_name,
                f"#{p.membership_id} ({p.membership.plan.name})",
                p.amount,
                p.get_method_display(),
                p.payment_date,
                p.received_by.username if p.received_by else "",
                p.notes,
            )
            for p in Payment.objects.select_related("membership__member", "membership__plan", "received_by")
        ],
    )

    # ── Asistencias de clientes ─────────────────────────────────────────────
    agregar_hoja(
        wb,
        "Asistencias",
        ["ID", "Cliente", "Check-in", "Check-out", "Duración (min)", "Registrado por"],
        [
            (
                a.id,
                a.member.full_name,
                a.check_in,
                a.check_out or "",
                int((a.check_out - a.check_in).total_seconds() // 60) if a.check_out else "En curso",
                a.registered_by.username if a.registered_by else "",
            )
            for a in Attendance.objects.select_related("member", "registered_by")
        ],
    )

    # ── Entrenadores ─────────────────────────────────────────────────────────
    agregar_hoja(
        wb,
        "Entrenadores",
        ["ID", "Nombre", "Apellido", "Especialidad", "Teléfono", "Activo", "Usuario vinculado"],
        [
            (
                c.id,
                c.first_name,
                c.last_name,
                c.specialty,
                c.phone,
                c.is_active,
                c.user.username if c.user else "",
            )
            for c in Coach.objects.all()
        ],
    )

    # ── Asistencias de entrenadores ──────────────────────────────────────────
    agregar_hoja(
        wb,
        "Asistencias entrenadores",
        ["ID", "Entrenador", "Check-in", "Check-out", "Duración (min)", "Registrado por"],
        [
            (
                a.id,
                a.coach.full_name,
                a.check_in,
                a.check_out or "",
                a.duration_minutes if a.duration_minutes is not None else "En curso",
                a.registered_by.username if a.registered_by else "",
            )
            for a in CoachAttendance.objects.select_related("coach", "registered_by")
        ],
    )

    return wb


def main() -> None:
    salida = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE_DIR / "complementos" / "datos_prueba.xlsx"
    salida.parent.mkdir(parents=True, exist_ok=True)

    wb = construir_libro()
    wb.save(salida)

    print(f"[OK] Datos de prueba exportados a: {salida}")
    print("     Hojas: " + ", ".join(ws.title for ws in wb.worksheets))


if __name__ == "__main__":
    main()
