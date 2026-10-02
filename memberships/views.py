from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import generics
from .models import Membership
from .serializers import MembershipSerializer
from members.views import IsAdminOrReceptionist

@extend_schema(
    tags=['memberships'],
    summary='Listar o asignar membresías',
    description='GET lista membresías; POST asigna un plan a un cliente (calcula end_date automáticamente).',
    parameters=[
        OpenApiParameter(
            name='member', type=OpenApiTypes.INT, required=False,
            description='Filtra membresías por ID de cliente',
        ),
    ],
)
class MembershipListCreateView(generics.ListCreateAPIView):
    """
    GET /api/memberships/ -> List all memberships
    POST /api/memberships/ -> Assign a membership
    """
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer
    permission_classes = [IsAdminOrReceptionist]

    def get_queryset(self):
        # Optional: Filter by member ID if provided in query params (?member=1)
        queryset = super().get_queryset()
        member_id = self.request.query_params.get('member')
        if member_id:
            queryset = queryset.filter(member_id=member_id)
        return queryset

@extend_schema(
    tags=['memberships'],
    summary='Detalle/actualizar una membresía',
    description='GET devuelve la membresía; PUT/PATCH permite cambiar el estado (ej. CANCELLED).',
)
class MembershipDetailView(generics.RetrieveUpdateAPIView):
    """
    GET /api/memberships/{id}/ -> View membership details
    PUT/PATCH /api/memberships/{id}/ -> Update membership (e.g. change status to CANCELLED)
    """
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer
    permission_classes = [IsAdminOrReceptionist]
