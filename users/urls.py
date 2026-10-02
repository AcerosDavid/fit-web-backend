from django.urls import path
from .views import LoginView, MeView, RefreshView, UserListCreateView, UserDetailView

urlpatterns = [
    # Auth routes
    path("auth/login/",   LoginView.as_view(),        name="auth-login"),
    path("auth/refresh/", RefreshView.as_view(),      name="auth-refresh"),
    path("auth/me/",      MeView.as_view(),            name="auth-me"),

    # User management routes (Admin only)
    path("users/",        UserListCreateView.as_view(), name="user-list"),
    path("users/<int:pk>/", UserDetailView.as_view(),  name="user-detail"),
]
