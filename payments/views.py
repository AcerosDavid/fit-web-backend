from rest_framework import generics
from .models import Payment
from .serializers import PaymentSerializer
from members.views import IsAdminOrReceptionist

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

class PaymentDetailView(generics.RetrieveUpdateAPIView):
    """
    GET /api/payments/{id}/ -> View payment details
    PUT/PATCH /api/payments/{id}/ -> Update payment details (e.g. notes)
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAdminOrReceptionist]
