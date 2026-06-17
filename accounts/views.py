"""Views for the accounts app."""

from rest_framework_simplejwt.views import TokenObtainPairView

from accounts.serializers import AdminTokenObtainPairSerializer


class AdminTokenObtainPairView(TokenObtainPairView):
    """Login endpoint that issues JWT access/refresh tokens carrying the role claim."""

    serializer_class = AdminTokenObtainPairSerializer
