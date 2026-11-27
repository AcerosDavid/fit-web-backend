"""
Manejo de archivos y reportes del gimnasio.

- Log diario de asistencias en archivos de texto JSON-lines
  (`logs/asistencia_YYYY-MM-DD.txt`), escrito en modo append.
- Exportación de pagos a Excel (.xlsx) con openpyxl.
- Lectura y verificación de los archivos generados.
"""

import json
from datetime import date, datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
REPORTS_DIR = BASE_DIR / "reportes"

ENCABEZADOS_PAGOS = [
    "ID", "Cliente", "Plan", "Fecha", "Método", "Monto", "Notas",
]


# ── Archivos de texto: log de asistencias ────────────────────────────────────

def ruta_log(fecha=None):
    """Ruta del archivo de log del día indicado (por defecto, hoy)."""
    fecha = fecha or date.today()
    return LOG_DIR / f"asistencia_{fecha.isoformat()}.txt"


def registrar_evento_asistencia(evento, fecha=None):
    """
    Agrega un evento de asistencia al log diario (modo 'a': append).

    `evento` es el diccionario devuelto por Persona.registrar_asistencia().
    Devuelve la ruta del archivo escrito.
    """
    ruta = ruta_log(fecha)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    linea = json.dumps(evento, ensure_ascii=False) + "\n"
    with open(ruta, "a", encoding="utf-8") as archivo:
        archivo.write(linea)
    return ruta


def leer_eventos(fecha=None):
    """
    Lee todos los eventos del log del día indicado.

    Si el archivo no existe devuelve una lista vacía (no lanza error).
    """
    ruta = ruta_log(fecha)
    if not ruta.exists():
        return []

    eventos = []
    with open(ruta, "r", encoding="utf-8") as archivo:
        for linea in archivo:
            linea = linea.strip()
            if linea:
                eventos.append(json.loads(linea))
    return eventos


def resumen_diario(fecha=None):
    """
    Resume el log del día: entradas, salidas y personas que siguen dentro.

    Devuelve un diccionario; si no hay archivo, los contadores son cero.
    """
    fecha = fecha or date.today()
    eventos = leer_eventos(fecha)

    entradas = [e for e in eventos if e.get("accion") == "check-in"]
    salidas = [e for e in eventos if e.get("accion") == "check-out"]

    # Personas con entrada pero sin salida posterior en el mismo día.
    dentro = {}
    for evento in eventos:
        qr = evento.get("qr_code")
        if not qr:
            continue
        registro = dentro.setdefault(qr, {
            "nombre": evento.get("nombre"),
            "tipo": evento.get("tipo"),
        })
        if evento.get("accion") == "check-in":
            registro["dentro"] = True
        elif evento.get("accion") == "check-out":
            registro["dentro"] = False

    personas_dentro = [
        f"{v['nombre']} ({v['tipo']})"
        for v in dentro.values() if v.get("dentro")
    ]

    return {
        "fecha": fecha.isoformat(),
        "archivo": str(ruta_log(fecha)),
        "total_entradas": len(entradas),
        "total_salidas": len(salidas),
        "personas_dentro": personas_dentro,
        "total_dentro": len(personas_dentro),
        "total_eventos": len(eventos),
    }


# ── Excel: exportación y lectura de pagos ────────────────────────────────────

def exportar_pagos_excel(filas, ruta_salida=None):
    """
    Escribe un archivo .xlsx con los pagos recibidos.

    `filas` es una lista de diccionarios con las claves:
        id, cliente, plan, fecha, metodo, monto, notas

    `ruta_salida` es opcional; por defecto se genera en `reportes/` con
    el nombre `pagos_YYYY-MM-DD.xlsx` (fecha actual).

    Devuelve la ruta (Path) del archivo generado.
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font

    if ruta_salida is None:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        ruta_salida = REPORTS_DIR / f"pagos_{date.today().isoformat()}.xlsx"
    ruta_salida = Path(ruta_salida)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)

    libro = Workbook()
    hoja = libro.active
    hoja.title = "Pagos"

    hoja.append(ENCABEZADOS_PAGOS)
    for celda in hoja[1]:
        celda.font = Font(bold=True)

    for fila in filas:
        hoja.append([
            fila.get("id"),
            fila.get("cliente"),
            fila.get("plan"),
            fila.get("fecha"),
            fila.get("metodo"),
            float(fila.get("monto") or 0),
            fila.get("notas") or "",
        ])

    libro.save(ruta_salida)
    return ruta_salida


def leer_excel(ruta):
    """
    Lee un archivo .xlsx y devuelve sus filas como lista de diccionarios
    usando la primera fila como encabezados. Cierra el libro al terminar.
    """
    from openpyxl import load_workbook

    libro = load_workbook(ruta, read_only=True, data_only=True)
    try:
        hoja = libro.active
        filas = hoja.iter_rows(values_only=True)
        encabezados = [str(h) if h is not None else "" for h in next(filas)]
        return [
            dict(zip(encabezados, fila))
            for fila in filas
            if any(valor is not None for valor in fila)
        ]
    finally:
        libro.close()


def filas_desde_pagos_queryset(queryset):
    """
    Convierte un queryset de `payments.Payment` en la lista de diccionarios
    que espera `exportar_pagos_excel()`.
    """
    return [
        {
            "id": pago.id,
            "cliente": pago.membership.member.full_name,
            "plan": pago.membership.plan.name,
            "fecha": timezone_str(pago.payment_date),
            "metodo": pago.get_method_display(),
            "monto": pago.amount,
            "notas": pago.notes,
        }
        for pago in queryset.select_related(
            "membership__member", "membership__plan",
        )
    ]


def timezone_str(valor):
    """Formatea un datetime/fecha como texto ISO para el Excel."""
    if isinstance(valor, datetime):
        return valor.isoformat(sep=" ", timespec="minutes")
    if isinstance(valor, date):
        return valor.isoformat()
    return str(valor)
