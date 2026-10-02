from rest_framework import serializers
from .models import Payment
from memberships.serializers import MembershipSerializer

class PaymentSerializer(serializers.ModelSerializer):
    membership_details = MembershipSerializer(source='membership', read_only=True)

    class Meta:
        model = Payment
        fields = (
            'id', 'membership', 'amount', 'payment_date', 'method', 
            'notes', 'received_by', 'membership_details',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'received_by', 'created_at', 'updated_at')

    def create(self, validated_data):
        # Automatically set received_by to the current user
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['received_by'] = request.user
        return super().create(validated_data)
