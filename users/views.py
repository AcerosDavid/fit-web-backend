from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User
from .serializers import CustomTokenObtainPairSerializer, RegisterUserSerializer, UserSerializer


class LoginView(TokenObtainPairView):
    """
    POST /api/auth/login/
    Body: { "username": "...", "password": "..." }
    Returns: { "access": "...", "refresh": "...", "user": { ... } }

    Equivalent to Laravel's: Auth::attempt($credentials)
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = (permissions.AllowAny,)


class MeView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/auth/me/     → Returns the authenticated user's data
    PUT  /api/auth/me/     → Updates the authenticated user's data
    PATCH /api/auth/me/    → Partial update

    Equivalent to Laravel's: Auth::user()
    """
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class UserListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/users/   → List all users (Admin only)
    POST /api/users/   → Create a new user (Admin only)
    """
    queryset = User.objects.all()
    serializer_class = RegisterUserSerializer
    permission_classes = (permissions.IsAdminUser,)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return UserSerializer
        return RegisterUserSerializer


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/users/{id}/  → Get a user by ID (Admin only)
    PUT    /api/users/{id}/  → Update a user (Admin only)
    DELETE /api/users/{id}/  → Delete a user (Admin only)
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAdminUser,)
