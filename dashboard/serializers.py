from rest_framework import serializers


class DashboardStatsSerializer(serializers.Serializer):
    """Métricas agregadas de GET /api/dashboard/."""

    active_members = serializers.IntegerField()
    monthly_revenue = serializers.FloatField()
    todays_attendance = serializers.IntegerField()
    expiring_memberships = serializers.IntegerField()
    month = serializers.CharField()
