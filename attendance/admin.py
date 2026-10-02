from django.contrib import admin
from .models import Attendance

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('member', 'check_in', 'check_out', 'registered_by')
    list_filter = ('check_in', 'check_out')
    search_fields = ('member__first_name', 'member__last_name')
