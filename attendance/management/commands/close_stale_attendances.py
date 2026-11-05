from django.core.management.base import BaseCommand

from attendance.models import Attendance
from attendance.services import close_stale_attendances
from coaches.models import CoachAttendance


class Command(BaseCommand):
    help = "Cierra las asistencias de clientes y entrenadores que quedaron abiertas de días anteriores"

    def handle(self, *args, **options):
        members = close_stale_attendances(Attendance.objects.all())
        coaches = close_stale_attendances(CoachAttendance.objects.all())
        self.stdout.write(self.style.SUCCESS(
            f"[OK] Cerradas {members} asistencias de clientes y {coaches} de entrenadores."
        ))
