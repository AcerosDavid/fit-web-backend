from rest_framework import serializers
from .models import Attendance
from members.serializers import MemberSerializer

class AttendanceSerializer(serializers.ModelSerializer):
    member_details = MemberSerializer(source='member', read_only=True)

    class Meta:
        model = Attendance
        fields = ('id', 'member', 'check_in', 'check_out', 'registered_by', 'member_details')
        read_only_fields = ('id', 'check_in', 'check_out', 'registered_by')

class CheckInSerializer(serializers.Serializer):
    member_id = serializers.IntegerField()
