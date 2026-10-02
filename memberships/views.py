from rest_framework import generics
from .models import Membership
from .serializers import MembershipSerializer
from members.views import IsAdminOrReceptionist

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

class MembershipDetailView(generics.RetrieveUpdateAPIView):
    """
    GET /api/memberships/{id}/ -> View membership details
    PUT/PATCH /api/memberships/{id}/ -> Update membership (e.g. change status to CANCELLED)
    """
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer
    permission_classes = [IsAdminOrReceptionist]
