from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_date

from core.reportes import exportar_pagos_excel, filas_desde_pagos_queryset, leer_excel
from payments.models import Payment


class Command(BaseCommand):
    """
    Exporta los pagos de un rango de fechas a un archivo Excel (.xlsx).

    Uso:
        python manage.py exportar_pagos_excel
        python manage.py exportar_pagos_excel --desde=2026-11-01 --hasta=2026-11-30
        python manage.py exportar_pagos_excel --salida=reportes/pagos.xlsx
    """

    help = "Genera un archivo Excel con los pagos registrados en un rango de fechas"

    def add_arguments(self, parser):
        parser.add_argument("--desde", dest="desde", default=None,
                            help="Fecha inicial YYYY-MM-DD (por defecto: sin límite).")
        parser.add_argument("--hasta", dest="hasta", default=None,
                            help="Fecha final YYYY-MM-DD (por defecto: sin límite).")
        parser.add_argument("--salida", dest="salida", default=None,
                            help="Ruta del .xlsx de salida (por defecto: reportes/pagos_<fecha>.xlsx).")

    def _parse_date(self, value, name):
        if not value:
            return None
        parsed = parse_date(value)
        if parsed is None:
            raise CommandError(f"{name} inválida: '{value}'. Use YYYY-MM-DD.")
        return parsed

    def handle(self, *args, **options):
        desde = self._parse_date(options["desde"], "--desde")
        hasta = self._parse_date(options["hasta"], "--hasta")
        if desde and hasta and desde > hasta:
            raise CommandError("--desde no puede ser posterior a --hasta.")

        queryset = Payment.objects.all()
        if desde:
            queryset = queryset.filter(payment_date__date__gte=desde)
        if hasta:
            queryset = queryset.filter(payment_date__date__lte=hasta)

        pagos = list(queryset.order_by("payment_date"))
        if not pagos:
            self.stdout.write(self.style.WARNING(
                "No hay pagos en el rango indicado; no se genera archivo."
            ))
            return

        filas = filas_desde_pagos_queryset(queryset)
        ruta = exportar_pagos_excel(filas, options["salida"])

        # Verificación: leer el archivo generado y comprobar el conteo.
        verificacion = leer_excel(ruta)

        total = sum(p.amount for p in pagos)
        self.stdout.write(self.style.SUCCESS(
            f"Excel generado: {ruta}"
        ))
        self.stdout.write(f"Pagos exportados: {len(filas)}")
        self.stdout.write(f"Filas verificadas al leer el archivo: {len(verificacion)}")
        self.stdout.write(f"Total exportado: ${total:,.2f}")
