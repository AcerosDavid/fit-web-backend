from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    """
    Ejecuta todos los seeders en el orden correcto.

    Uso:
        python manage.py seed_all
        python manage.py seed_all --flush   (ademas limpia usuarios y miembros)
        python manage.py seed_all --count=50
    """

    help = "Ejecuta todos los seeders en orden: users, members, plans, memberships, payments, attendance"

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Elimina datos de pago/asistencia/membresia, miembros y usuarios antes de sembrar.",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=100,
            help="Cantidad de miembros a crear (default: 100).",
        )

    @transaction.atomic
    def flush_related(self):
        from attendance.models import Attendance
        from memberships.models import Membership
        from payments.models import Payment

        self.stdout.write(self.style.WARNING("[!] Limpiando pagos, asistencias y membresias..."))
        Payment.objects.all().delete()
        Attendance.objects.all().delete()
        Membership.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("    Datos relacionados eliminados.\n"))

    def handle(self, *args, **options):
        flush = options["flush"]

        if flush:
            self.flush_related()

        steps = [
            ("seed", ["seed"] + (["--flush"] if flush else [])),
            ("seed_members", ["seed_members", f"--count={options['count']}"] + (["--flush"] if flush else [])),
            ("seed_plans", ["seed_plans"]),
            ("seed_memberships", ["seed_memberships"]),
            ("seed_payments", ["seed_payments"]),
            ("seed_attendance", ["seed_attendance"]),
        ]

        for index, (name, args) in enumerate(steps, start=1):
            self.stdout.write(self.style.MIGRATE_HEADING(f"\n[{index}/{len(steps)}] {name}"))
            call_command(*args)

        self.stdout.write(self.style.SUCCESS("\n[OK] Todos los seeders ejecutados.\n"))
