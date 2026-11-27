#!/usr/bin/env python
"""
Genera el diccionario de datos del proyecto en formato Excel.

Uso (desde la raíz del proyecto):
    python scripts/generar_diccionario_datos.py [ruta_salida]

Salida por defecto:
    complementos/diccionario_datos.xlsx

El script recorre todos los modelos instalados en Django y describe cada
tabla, cada campo, su tipo, restricciones y relaciones. No modifica la base
de datos: solo la consulta.
"""
import os
import sys
from pathlib import Path

import django

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django.setup()

from django.conf import settings  # noqa: E402

from django.apps import apps  # noqa: E402
from openpyxl import Workbook  # noqa: E402
from openpyxl.styles import Alignment, Font, PatternFill  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402

# Apps propias del proyecto (las de terceros no interesan en el diccionario).
APLICACIONES_PROYECTO = [
    "attendance",
    "coaches",
    "dashboard",
    "members",
    "memberships",
    "payments",
    "plans",
    "users",
]

ENCABEZADO = PatternFill("solid", fgColor="1F4E79")
ENCABEZADO_LETRA = Font(color="FFFFFF", bold=True)


def tipo_campo(field) -> str:
    """Nombre legible del tipo de dato de un campo."""
    return type(field).__name__.replace("Field", "").strip() or "Char"


def detalle_tipo(field) -> str:
    """Detalle del tipo: longitud, decimales, relación u opciones."""
    if field.is_relation:
        relacion = f"{field.related_model._meta.app_label}.{field.related_model.__name__}"
        extra = ""
        if hasattr(field, "remote_field") and field.remote_field:
            if getattr(field.remote_field, "on_delete", None) is not None:
                extra = f" (on_delete={getattr(field.remote_field.on_delete, '__name__', field.remote_field.on_delete)})"
        return f"{tipo_campo(field)} → {relacion}{extra}"

    detalles = []
    if getattr(field, "max_length", None):
        detalles.append(f"max_length={field.max_length}")
    if getattr(field, "decimal_places", None) is not None and getattr(field, "max_digits", None):
        detalles.append(f"max_digits={field.max_digits}, decimal_places={field.decimal_places}")
    if getattr(field, "choices", None):
        detalles.append("choices=" + " | ".join(f"{valor}" for valor, _ in field.choices))
    return f"{tipo_campo(field)}" + (f" ({', '.join(detalles)})" if detalles else "")


def restricciones(field) -> str:
    """Restricciones aplicables al campo (null, unique, índice primario...)."""
    partes = []
    if field.primary_key:
        partes.append("PK")
    if not field.null:
        partes.append("NOT NULL")
    else:
        partes.append("nullable")
    if field.unique:
        partes.append("UNIQUE")
    if field.db_index:
        partes.append("INDEX")
    if getattr(field, "blank", False) and not field.primary_key:
        partes.append("blank=True")
    if field.has_default():
        partes.append(f"default={field.get_default()!r}")
    return ", ".join(partes)


def obtener_modelos():
    """Lista los modelos del proyecto (excluye las apps de terceros)."""
    modelos = []
    for app_config in apps.get_app_configs():
        if app_config.label not in APLICACIONES_PROYECTO:
            continue
        for model in app_config.get_models():
            modelos.append((app_config.label, model))
    return sorted(modelos, key=lambda item: (item[0], item[1].__name__))


def construir_libro() -> Workbook:
    wb = Workbook()

    # ── Hoja 1: Modelos ─────────────────────────────────────────────────────
    ws_modelos = wb.active
    ws_modelos.title = "Modelos"
    ws_modelos.append(["Aplicación", "Modelo (clase)", "Tabla", "Registros*", "Descripción"])

    # ── Hoja 2: Campos ──────────────────────────────────────────────────────
    ws_campos = wb.create_sheet("Campos")
    ws_campos.append([
        "Aplicación",
        "Modelo (clase)",
        "Tabla",
        "Campo",
        "Tipo",
        "Detalle del tipo",
        "Descripción",
        "Restricciones",
        "Campo relacionado",
    ])

    # ── Hoja 3: Relaciones ───────────────────────────────────────────────────
    ws_rel = wb.create_sheet("Relaciones")
    ws_rel.append([
        "Aplicación",
        "Modelo origen",
        "Campo FK / OneToOne",
        "Modelo destino",
        "Tipo de relación",
        "related_name",
        "on_delete",
    ])

    for app_label, model in obtener_modelos():
        meta = model._meta
        try:
            total = model._default_manager.count()
        except Exception:  # pragma: no cover - tablas sin migrar no deberían existir
            total = "-"

        ws_modelos.append([
            app_label,
            model.__name__,
            meta.db_table,
            total,
            (model._meta.verbose_name + " / " + model._meta.verbose_name_plural),
        ])

        for field in meta.get_fields():
            es_relacion = getattr(field, "is_relation", False)
            if es_relacion and not hasattr(field, "column"):
                # Relación inversa (related_name): se documenta en la hoja Relaciones
                continue

            nombre_campo = getattr(field, "name", str(field))
            campo_relacionado = ""
            if es_relacion and hasattr(field, "related_model") and field.related_model:
                campo_relacionado = f"{field.related_model._meta.app_label}.{field.related_model.__name__}"
                if getattr(field, "remote_field", None) is not None and field.remote_field:
                    campo_relacionado += f" (campo {field.target_field.name})"

            ws_campos.append([
                app_label,
                model.__name__,
                meta.db_table,
                nombre_campo,
                tipo_campo(field),
                detalle_tipo(field),
                str(getattr(field, "verbose_name", "") or ""),
                restricciones(field),
                campo_relacionado,
            ])

            if es_relacion and hasattr(field, "related_model") and field.related_model:
                if field.many_to_many or field.one_to_many:
                    tipo_rel = "Muchos a muchos" if field.many_to_many else "Uno a muchos (reverse)"
                elif field.one_to_one:
                    tipo_rel = "Uno a uno"
                else:
                    tipo_rel = "Muchos a uno (FK)"
                remote = getattr(field, "remote_field", None)
                ws_rel.append([
                    app_label,
                    model.__name__,
                    nombre_campo,
                    f"{field.related_model._meta.app_label}.{field.related_model.__name__}",
                    tipo_rel,
                    getattr(remote, "related_name", None) or "-",
                    getattr(getattr(remote, "on_delete", None), "__name__", "-"),
                ])

    for ws in (ws_modelos, ws_campos, ws_rel):
        for cell in ws[1]:
            cell.fill = ENCABEZADO
            cell.font = ENCABEZADO_LETRA
            cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        for columna in ws.columns:
            ancho = max(len(str(celda.value)) if celda.value is not None else 0 for celda in columna)
            ws.column_dimensions[get_column_letter(columna[0].column)].width = min(max(ancho + 2, 12), 60)

    return wb


def main() -> None:
    salida = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE_DIR / "complementos" / "diccionario_datos.xlsx"
    salida.parent.mkdir(parents=True, exist_ok=True)

    wb = construir_libro()
    wb.save(salida)

    hojas = ", ".join(ws.title for ws in wb.worksheets)
    print(f"[OK] Diccionario de datos generado en: {salida}")
    print(f"     Hojas: {hojas}")
    print(f"     Base de datos: {settings.DATABASES['default']['NAME']}")


if __name__ == "__main__":
    main()
