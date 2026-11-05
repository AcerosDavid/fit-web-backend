from rest_framework import serializers

from .models import Coach, CoachAttendance


class CoachSerializer(serializers.ModelSerializer):
    qr_code = serializers.CharField(read_only=True)

    class Meta:
        model = Coach
        fields = (
            'id', 'user', 'first_name', 'last_name', 'qr_code', 'specialty',
            'phone', 'bio', 'is_active', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'qr_code', 'created_at', 'updated_at')


class CoachAttendanceSerializer(serializers.ModelSerializer):
    duration_minutes = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = CoachAttendance
        fields = (
            'id', 'coach', 'check_in', 'check_out', 'duration_minutes',
            'registered_by',
        )
        read_only_fields = (
            'id', 'coach', 'check_in', 'check_out', 'duration_minutes',
            'registered_by',
        )


class CoachHistorySummarySerializer(serializers.Serializer):
    total_attendances = serializers.IntegerField()
    total_minutes = serializers.IntegerField()
    currently_inside = serializers.BooleanField()
    open_attendance_id = serializers.IntegerField(allow_null=True)
    first_attendance = serializers.DateTimeField(allow_null=True)
    last_attendance = serializers.DateTimeField(allow_null=True)


class CoachHistorySerializer(serializers.Serializer):
    coach = CoachSerializer()
    summary = CoachHistorySummarySerializer()
    attendances = CoachAttendanceSerializer(many=True)
