from django.db import models
from django.utils import timezone
from memberships.models import Membership
from django.conf import settings

class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = 'CASH', 'Efectivo'
        CARD = 'CARD', 'Tarjeta'
        TRANSFER = 'TRANSFER', 'Transferencia'

    membership = models.ForeignKey(Membership, on_delete=models.PROTECT, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(default=timezone.now)
    method = models.CharField(max_length=20, choices=Method.choices, default=Method.CASH)
    notes = models.TextField(blank=True)
    
    # Audit trail
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='received_payments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"{self.membership.member.full_name} - ${self.amount} ({self.get_method_display()})"
