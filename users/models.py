from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administrador"
        RECEPTIONIST = "RECEPTIONIST", "Recepcionista"

    role = models.CharField(
        max_length=50, 
        choices=Role.choices, 
        default=Role.RECEPTIONIST
    )

    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"
