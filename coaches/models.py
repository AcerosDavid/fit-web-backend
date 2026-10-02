from django.db import models
from django.conf import settings

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
