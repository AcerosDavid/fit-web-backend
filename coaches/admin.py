from django.contrib import admin
from .models import Coach

@admin.register(Coach)
class CoachAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'specialty', 'phone', 'is_active')
    list_filter = ('is_active', 'specialty')
    search_fields = ('first_name', 'last_name', 'specialty')
