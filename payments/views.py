from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import generics
from .models import Payment
from .serializers import PaymentSerializer
from members.views import IsAdminOrReceptionist

@extend_schema(
    tags=['payments'],
    summary='Listar o registrar pagos',
    description='GET lista cobros; POST registra un cobro (efectivo, tarjeta o transferencia).',
    parameters=[
        OpenApiParameter(
            name='membership', type=OpenApiTypes.INT, required=False,
            description='Filtra pagos por ID de membresía',
        ),
        OpenApiParameter(
            name='member', type=OpenApiTypes.INT, required=False,
            description='Filtra pagos por ID de cliente',
        ),
    ],
)
class PaymentListCreateView(generics.ListCreateAPIView):
    """
    GET /api/payments/ -> List all payments
    POST /api/payments/ -> Register a payment
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAdminOrReceptionist]

    def get_queryset(self):
        # Filter by membership ID or member ID if provided
        queryset = super().get_queryset()
        membership_id = self.request.query_params.get('membership')
        member_id = self.request.query_params.get('member')
        
        if membership_id:
            queryset = queryset.filter(membership_id=membership_id)
        if member_id:
            queryset = queryset.filter(membership__member_id=member_id)
            
        return queryset

@extend_schema(
    tags=['payments'],
    summary='Detalle/actualizar un pago',
    description='GET devuelve el pago; PUT/PATCH permite corregir datos (ej. notas).',
)
class PaymentDetailView(generics.RetrieveUpdateAPIView):
    """
    GET /api/payments/{id}/ -> View payment details
    PUT/PATCH /api/payments/{id}/ -> Update payment details (e.g. notes)
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAdminOrReceptionist]
