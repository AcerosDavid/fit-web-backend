from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .models import User
from .serializers import (
    CustomTokenObtainPairSerializer,
    LoginResponseSerializer,
    RefreshResponseSerializer,
    RegisterUserSerializer,
    UserSerializer,
)


class LoginView(TokenObtainPairView):
    """
    POST /api/auth/login/
    Body: { "username": "...", "password": "..." }
    Returns: { "access": "...", "refresh": "...", "user": { ... } }

    Equivalent to Laravel's: Auth::attempt($credentials)
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        tags=['auth'],
        summary='Iniciar sesión',
        description=(
            'Autentica con username/password y devuelve los tokens JWT '
            'más el perfil del usuario. Usa `access` en '
            '`Authorization: Bearer <token>`.'
        ),
        responses={200: LoginResponseSerializer},
        auth=[],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class RefreshView(TokenRefreshView):
    """POST /api/auth/refresh/ -> Nuevo par access/refresh (rotación)."""

    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        tags=['auth'],
        summary='Refrescar tokens',
        description=(
            'Intercambia un `refresh` válido por un nuevo par '
            '`access` + `refresh` (ROTATE_REFRESH_TOKENS=True).'
        ),
        request={'refresh': str},
        responses={200: RefreshResponseSerializer},
        auth=[],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


@extend_schema(
    tags=['auth'],
    summary='Obtener/actualizar el perfil propio',
    description='GET devuelve los datos del usuario autenticado; PUT/PATCH los actualizan (sin password).',
)
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


@extend_schema(
    tags=['users'],
    summary='Listar o crear usuarios del staff',
    description='GET requiere rol Admin. El password se envía write-only (mínimo 8 caracteres).',
)
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


@extend_schema(
    tags=['users'],
    summary='Detalle/actualizar/eliminar un usuario',
    description='Operaciones sobre un usuario por ID (solo Admin).',
)
class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/users/{id}/  → Get a user by ID (Admin only)
    PUT    /api/users/{id}/  → Update a user (Admin only)
    DELETE /api/users/{id}/  → Delete a user (Admin only)
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAdminUser,)
