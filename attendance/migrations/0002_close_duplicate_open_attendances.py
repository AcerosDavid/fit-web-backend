from datetime import datetime, time

from django.db import migrations
from django.utils import timezone


def close_duplicate_open_attendances(apps, schema_editor):
    """Deja abierta solo la asistencia más reciente de cada cliente."""
    Attendance = apps.get_model('attendance', 'Attendance')
    seen = set()
    open_attendances = Attendance.objects.filter(check_out__isnull=True).order_by('member_id', '-check_in')
    for attendance in open_attendances:
        if attendance.member_id not in seen:
            seen.add(attendance.member_id)
            continue
        local = timezone.localtime(attendance.check_in)
        attendance.check_out = datetime.combine(local.date(), time(23, 59, 59), tzinfo=local.tzinfo)
        attendance.save(update_fields=['check_out'])


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(close_duplicate_open_attendances, migrations.RunPython.noop),
    ]
