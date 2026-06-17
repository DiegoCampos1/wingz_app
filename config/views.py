"""Project-level views that are not tied to a specific app."""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    """Lightweight liveness probe used by Docker and uptime checks."""
    return Response({"status": "ok"})
