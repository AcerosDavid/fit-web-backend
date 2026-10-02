from django.contrib import admin
from .models import Member


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "phone", "status", "created_at")
    list_filter = ("status", "gender")
    search_fields = ("first_name", "last_name", "email", "phone")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Personal Information", {
            "fields": ("first_name", "last_name", "email", "phone", "date_of_birth", "gender")
        }),
        ("Account Status", {
            "fields": ("status",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
