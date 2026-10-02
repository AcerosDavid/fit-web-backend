from drf_spectacular.utils import extend_schema
from rest_framework import generics
from .models import Coach
from .serializers import CoachSerializer
from members.views import IsAdminOrReceptionist

@extend_schema(
    tags=['coaches'],
    summary='Listar o crear entrenadores',
    description='GET lista los entrenadores activos; POST crea uno.',
)
class CoachListCreateView(generics.ListCreateAPIView):
    """
    GET /api/coaches/ -> List all coaches
    POST /api/coaches/ -> Create a coach
    """
    queryset = Coach.objects.filter(is_active=True)
    serializer_class = CoachSerializer
    permission_classes = [IsAdminOrReceptionist]

@extend_schema(
    tags=['coaches'],
    summary='Detalle/actualizar/eliminar un entrenador',
    description='DELETE hace soft-delete (is_active=False) para conservar el historial.',
)
class CoachDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/coaches/{id}/ -> View coach details
    PUT/PATCH /api/coaches/{id}/ -> Edit coach
    DELETE /api/coaches/{id}/ -> Delete (soft/hard depending on logic)
    """
    queryset = Coach.objects.all()
    serializer_class = CoachSerializer
    permission_classes = [IsAdminOrReceptionist]

    def perform_destroy(self, instance):
        # Soft delete coach
        instance.is_active = False
        instance.save()
