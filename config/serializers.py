from rest_framework import serializers


class DetailMessageSerializer(serializers.Serializer):
    """Respuesta genérica: {"detail": "..."}"""

    detail = serializers.CharField()


class ErrorMessageSerializer(serializers.Serializer):
    """Respuesta de error: {"error": "..."} (+ attendance_id opcional)."""

    error = serializers.CharField()
    attendance_id = serializers.IntegerField(required=False)
