from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    """Endpoint público de salud, pensado para healthchecks de Docker/orquestadores."""

    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['health'],
        summary='Estado del servicio',
        description='Devuelve `{"status": "ok"}` si la API y la base de datos responden. No requiere autenticación.',
        responses={200: OpenApiTypes.OBJECT},
        auth=[],  # tipo de autenticación
    )
    def get(self, request):
        return Response({'status': 'ok'})
