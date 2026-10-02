from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for reading user data. Never exposes the password."""

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "role", "is_active")
        read_only_fields = ("id",)


class RegisterUserSerializer(serializers.ModelSerializer):
    """Serializer for creating new users (admin only)."""

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("username", "email", "password", "first_name", "last_name", "role")

    def create(self, validated_data):
        # Use set_password to hash the password correctly
        user = User(**validated_data)
        user.set_password(validated_data["password"])
        user.save()
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extends the default JWT login response to include user info.
    Instead of returning only { access, refresh },
    returns: { access, refresh, user: { id, username, role, ... } }
    """

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data
