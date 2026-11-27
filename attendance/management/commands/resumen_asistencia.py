from datetime import date

from django.core.management.base import BaseCommand, CommandError

from core.reportes import resumen_diario


class Command(BaseCommand):
    """
    Muestra el resumen del log diario de asistencias.

    Uso:
        python manage.py resumen_asistencia
        python manage.py resumen_asistencia --date=2026-11-26
    """

    help = "Resume las entradas/salidas registradas en el log diario de asistencias"

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            dest="fecha",
            default=None,
            help="Fecha del log en formato YYYY-MM-DD (por defecto: hoy).",
        )

    def handle(self, *args, **options):
        fecha = None
        if options["fecha"]:
            try:
                fecha = date.fromisoformat(options["fecha"])
            except ValueError:
                raise CommandError(
                    f"Fecha inválida: '{options['fecha']}'. Use YYYY-MM-DD."
                )

        resumen = resumen_diario(fecha)

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Resumen de asistencias — {resumen['fecha']}"
        ))
        self.stdout.write(f"Archivo: {resumen['archivo']}")
        self.stdout.write(f"Entradas: {resumen['total_entradas']}")
        self.stdout.write(f"Salidas:   {resumen['total_salidas']}")
        self.stdout.write(f"Dentro del gimnasio ahora: {resumen['total_dentro']}")

        for persona in resumen["personas_dentro"]:
            self.stdout.write(f"  - {persona}")

        if resumen["total_eventos"] == 0:
            self.stdout.write(self.style.WARNING(
                "  (No hay eventos registrados para esta fecha.)"
            ))
