from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions
from .models import Plan
from .serializers import PlanSerializer
from members.views import IsAdminOrReceptionist

@extend_schema(
    tags=['plans'],
    summary='Listar o crear planes',
    description='GET: admin o recepción. POST: solo admin.',
)
class PlanListCreateView(generics.ListCreateAPIView):
    """
    GET /api/plans/  -> List plans
    POST /api/plans/ -> Create plan
    """
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAdminOrReceptionist()]
        return [permissions.IsAdminUser()]

@extend_schema(
    tags=['plans'],
    summary='Detalle/actualizar/eliminar un plan',
    description='GET: admin o recepción. PUT/PATCH/DELETE: solo admin.',
)
class PlanDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/plans/{id}/ -> View plan
    PUT/PATCH /api/plans/{id}/ -> Edit plan
    DELETE /api/plans/{id}/ -> Delete plan
    """
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAdminOrReceptionist()]
        return [permissions.IsAdminUser()]
