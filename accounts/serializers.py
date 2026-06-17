"""Serializers for the accounts app."""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from accounts.models import User
from common.serializers import StrictFieldsModelSerializer


class AdminTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT serializer that embeds the user's role as a token claim."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        return token


class UserSerializer(serializers.ModelSerializer):
    """Read serializer for users."""

    class Meta:
        model = User
        fields = ["id_user", "role", "first_name", "last_name", "email", "phone_number"]


class UserWriteSerializer(StrictFieldsModelSerializer):
    """Base write serializer that handles password hashing."""

    class Meta:
        model = User
        fields = [
            "id_user",
            "role",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "password",
        ]
        read_only_fields = ["id_user"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UserCreateSerializer(UserWriteSerializer):
    """Create serializer (password required)."""


class UserUpdateSerializer(UserWriteSerializer):
    """Update serializer (password optional)."""

    password = serializers.CharField(write_only=True, required=False)
