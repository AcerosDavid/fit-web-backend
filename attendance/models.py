from django.db import models
from django.utils import timezone
from members.models import Member
from django.conf import settings

class Attendance(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='attendances')
    check_in = models.DateTimeField(default=timezone.now)
    check_out = models.DateTimeField(null=True, blank=True)
    
    # Audit trail
    registered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='registered_attendances')

    class Meta:
        ordering = ['-check_in']

    def __str__(self):
        return f"{self.member.full_name} - In: {self.check_in.strftime('%Y-%m-%d %H:%M')}"
