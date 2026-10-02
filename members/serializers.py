from rest_framework import serializers
from .models import Member


class MemberSerializer(serializers.ModelSerializer):
    """Serializer for reading member data."""

    full_name = serializers.CharField(read_only=True)
    is_deleted = serializers.BooleanField(read_only=True)

    class Meta:
        model = Member
        fields = (
            "id",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "phone",
            "date_of_birth",
            "gender",
            "status",
            "is_deleted",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class MemberCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating members."""

    class Meta:
        model = Member
        fields = (
            "first_name",
            "last_name",
            "email",
            "phone",
            "date_of_birth",
            "gender",
            "status",
        )
