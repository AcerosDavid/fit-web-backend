from rest_framework import serializers
from .models import Membership
from plans.serializers import PlanSerializer
from members.serializers import MemberSerializer

class MembershipSerializer(serializers.ModelSerializer):
    # Nested serializers for reading
    member_details = MemberSerializer(source='member', read_only=True)
    plan_details = PlanSerializer(source='plan', read_only=True)
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = Membership
        fields = (
            'id', 'member', 'plan', 'start_date', 'end_date', 'status', 
            'is_valid', 'created_by', 'member_details', 'plan_details',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'end_date', 'created_by', 'created_at', 'updated_at')

    def create(self, validated_data):
        # Automatically set created_by to the current user
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)
