from django.db import models
from django.conf import settings
from django.utils import timezone


class Coach(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='coach_profile',
        null=True, 
        blank=True,
        help_text="Usuario de sistema asociado (opcional)"
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    specialty = models.CharField(max_length=150, help_text="Ej: Pesas, Crossfit, Zumba")
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['first_name', 'last_name']
        verbose_name_plural = "Coaches"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.specialty})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def qr_code(self):
        """Código que se codifica en el QR de acceso del entrenador."""
        return f"FIT-C-{self.id}"


class CoachAttendance(models.Model):
    coach = models.ForeignKey(Coach, on_delete=models.CASCADE, related_name='attendances')
    check_in = models.DateTimeField(default=timezone.now)
    check_out = models.DateTimeField(null=True, blank=True)

    # Audit trail
    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='registered_coach_attendances',
    )

    class Meta:
        ordering = ['-check_in']
        constraints = [
            models.UniqueConstraint(
                fields=['coach'],
                condition=models.Q(check_out__isnull=True),
                name='unique_open_attendance_per_coach',
            ),
        ]

    def __str__(self):
        return f"{self.coach.full_name} - In: {self.check_in.strftime('%Y-%m-%d %H:%M')}"

    @property
    def duration_minutes(self):
        if self.check_out and self.check_in:
            return int((self.check_out - self.check_in).total_seconds() // 60)
        return None
