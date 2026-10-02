from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import LoginView, MeView, UserListCreateView, UserDetailView

urlpatterns = [
    # Auth routes
    path("auth/login/",   LoginView.as_view(),        name="auth-login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("auth/me/",      MeView.as_view(),            name="auth-me"),

    # User management routes (Admin only)
    path("users/",        UserListCreateView.as_view(), name="user-list"),
    path("users/<int:pk>/", UserDetailView.as_view(),  name="user-detail"),
]
