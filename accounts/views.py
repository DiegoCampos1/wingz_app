"""Views for the accounts app."""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView

from accounts.models import User
from accounts.permissions import IsAdminRole
from accounts.serializers import (
    AdminTokenObtainPairSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


class AdminTokenObtainPairView(TokenObtainPairView):
    """Login endpoint that issues JWT access/refresh tokens carrying the role claim."""

    serializer_class = AdminTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    """Admin-only CRUD for users."""

    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ("update", "partial_update"):
            return UserUpdateSerializer
        return UserSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return User.objects.none()
        return User.objects.order_by("id_user")
