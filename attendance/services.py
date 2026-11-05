from datetime import datetime, time

from django.db import IntegrityError, transaction
from django.utils import timezone

END_OF_DAY = time(23, 59, 59)


def end_of_local_day(value):
    """Último segundo del día local (TIME_ZONE) al que pertenece `value`."""
    local = timezone.localtime(value)
    return datetime.combine(local.date(), END_OF_DAY, tzinfo=local.tzinfo)


def check_out_time(attendance, now=None):
    """Ahora, o el final del día de entrada si la asistencia quedó abierta de otro día."""
    now = now or timezone.now()
    return min(now, end_of_local_day(attendance.check_in))


def close_stale_attendances(queryset, today=None):
    """Cierra las asistencias abiertas de días anteriores al final de su día de entrada."""
    today = today or timezone.localdate()
    start_of_today = timezone.make_aware(datetime.combine(today, time.min))
    closed = 0
    for attendance in queryset.filter(check_out__isnull=True, check_in__lt=start_of_today):
        attendance.check_out = end_of_local_day(attendance.check_in)
        attendance.save(update_fields=['check_out'])
        closed += 1
    return closed


def get_open_attendance(queryset):
    """Asistencia abierta de hoy, tras cerrar las que quedaron abiertas de días anteriores."""
    close_stale_attendances(queryset)
    return queryset.filter(check_out__isnull=True).first()


def create_attendance(model, **fields):
    """Crea la asistencia, o devuelve None si ya existe una abierta (restricción única)."""
    try:
        with transaction.atomic():
            return model.objects.create(check_in=timezone.now(), **fields)
    except IntegrityError:
        return None
