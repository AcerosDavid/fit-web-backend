from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from config.serializers import DetailMessageSerializer
from .models import Member
from .serializers import MemberSerializer, MemberCreateUpdateSerializer


class IsAdminOrReceptionist(permissions.BasePermission):
    """
    Custom permission: allows access to Admin and Receptionist roles.
    Equivalent to a middleware/gate in Laravel.
    """

    def has_permission(self, request, view):
        from users.models import User
        return request.user.role in (User.Role.ADMIN, User.Role.RECEPTIONIST)


@extend_schema(
    tags=['members'],
    summary='Listar o crear clientes',
    description='GET devuelve solo los clientes activos (excluye los soft-deletados). POST crea un cliente.',
)
class MemberListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/members/   → List all active members (not soft-deleted)
    POST /api/members/   → Create a new member
    """
    queryset = Member.objects.all()   # SoftDeleteManager already excludes deleted
    permission_classes = (IsAdminOrReceptionist,)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return MemberCreateUpdateSerializer
        return MemberSerializer


@extend_schema(
    tags=['members'],
    summary='Detalle/actualizar un cliente',
    description='GET devuelve el cliente; PUT/PATCH actualizan (serializer de creación/edición).',
)
class MemberDetailView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/members/{id}/   → Get member details
    PUT   /api/members/{id}/   → Full update
    PATCH /api/members/{id}/   → Partial update
    """
    queryset = Member.objects.all()
    permission_classes = (IsAdminOrReceptionist,)

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return MemberCreateUpdateSerializer
        return MemberSerializer


@extend_schema(
    tags=['members'],
    summary='Soft-delete de un cliente',
    description='Marca el cliente como eliminado (deleted_at) sin borrar su historial contable.',
    responses={200: DetailMessageSerializer, 404: DetailMessageSerializer},
)
class MemberDeleteView(APIView):
    """
    DELETE /api/members/{id}/delete/  → Soft delete a member
    """
    permission_classes = (IsAdminOrReceptionist,)

    def delete(self, request, pk):
        try:
            member = Member.objects.get(pk=pk)
        except Member.DoesNotExist:
            return Response({"detail": "Member not found."}, status=status.HTTP_404_NOT_FOUND)

        member.delete()   # Soft delete (sets deleted_at)
        return Response({"detail": f"Member '{member.full_name}' has been deactivated."}, status=status.HTTP_200_OK)


@extend_schema(
    tags=['members'],
    summary='Restaurar un cliente eliminado',
    description='Revierte el soft-delete. Devuelve 400 si el cliente no estaba eliminado.',
    request=None,  # POST sin cuerpo
    responses={200: MemberSerializer, 400: DetailMessageSerializer, 404: DetailMessageSerializer},
)
class MemberRestoreView(APIView):
    """
    POST /api/members/{id}/restore/  → Restore a soft-deleted member
    """
    permission_classes = (permissions.IsAdminUser,)

    def post(self, request, pk):
        try:
            member = Member.all_objects.get(pk=pk)
        except Member.DoesNotExist:
            return Response({"detail": "Member not found."}, status=status.HTTP_404_NOT_FOUND)

        if not member.is_deleted:
            return Response({"detail": "Member is not deleted."}, status=status.HTTP_400_BAD_REQUEST)

        member.restore()
        return Response(MemberSerializer(member).data, status=status.HTTP_200_OK)
