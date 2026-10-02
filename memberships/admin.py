from django.contrib import admin
from .models import Membership

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('member', 'plan', 'start_date', 'end_date', 'status', 'is_valid')
    list_filter = ('status', 'plan')
    search_fields = ('member__first_name', 'member__last_name', 'member__email')
    readonly_fields = ('created_at', 'updated_at', 'end_date')
