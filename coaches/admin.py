from django.contrib import admin

from .models import Coach, CoachAttendance


@admin.register(Coach)
class CoachAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'specialty', 'phone', 'is_active')
    list_filter = ('is_active', 'specialty')
    search_fields = ('first_name', 'last_name', 'specialty')


@admin.register(CoachAttendance)
class CoachAttendanceAdmin(admin.ModelAdmin):
    list_display = ('coach', 'check_in', 'check_out', 'registered_by')
    list_filter = ('check_in', 'check_out')
    search_fields = ('coach__first_name', 'coach__last_name')
