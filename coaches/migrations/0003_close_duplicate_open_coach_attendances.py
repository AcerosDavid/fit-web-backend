from datetime import datetime, time

from django.db import migrations
from django.utils import timezone


def close_duplicate_open_attendances(apps, schema_editor):
    """Deja abierta solo la asistencia más reciente de cada entrenador."""
    CoachAttendance = apps.get_model('coaches', 'CoachAttendance')
    seen = set()
    open_attendances = CoachAttendance.objects.filter(check_out__isnull=True).order_by('coach_id', '-check_in')
    for attendance in open_attendances:
        if attendance.coach_id not in seen:
            seen.add(attendance.coach_id)
            continue
        local = timezone.localtime(attendance.check_in)
        attendance.check_out = datetime.combine(local.date(), time(23, 59, 59), tzinfo=local.tzinfo)
        attendance.save(update_fields=['check_out'])


class Migration(migrations.Migration):

    dependencies = [
        ('coaches', '0002_coachattendance'),
    ]

    operations = [
        migrations.RunPython(close_duplicate_open_attendances, migrations.RunPython.noop),
    ]
