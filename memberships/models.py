from django.db import models
from datetime import timedelta
from django.utils import timezone
from members.models import Member
from plans.models import Plan
from django.conf import settings

class Membership(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        EXPIRED = 'EXPIRED', 'Expired'
        CANCELLED = 'CANCELLED', 'Cancelled'

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='memberships')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='memberships')
    
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    
    # Audit trail
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_memberships')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.member.full_name} - {self.plan.name} ({self.status})"

    def save(self, *args, **kwargs):
        # Calculate end_date automatically if not provided
        if not self.end_date and self.plan:
            self.end_date = self.start_date + timedelta(days=self.plan.duration_days)
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        return self.status == self.Status.ACTIVE and self.end_date >= timezone.now().date()
