from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('membership', 'amount', 'payment_date', 'method', 'received_by')
    list_filter = ('method', 'payment_date')
    search_fields = ('membership__member__first_name', 'membership__member__last_name')
    readonly_fields = ('created_at', 'updated_at')
