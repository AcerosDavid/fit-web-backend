"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from config.views import HealthView

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/health/', HealthView.as_view(), name='health'),

    # Documentación OpenAPI (Swagger)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # API v1 - all routes prefixed with /api/
    path('api/', include('users.urls')),
    path('api/', include('members.urls')),
    path('api/', include('plans.urls')),
    path('api/', include('memberships.urls')),
    path('api/', include('payments.urls')),
    path('api/', include('attendance.urls')),
    path('api/', include('dashboard.urls')),
    path('api/', include('coaches.urls')),
]
