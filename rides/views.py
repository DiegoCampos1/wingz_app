"""ViewSets for the rides app."""

from datetime import timedelta

from django.db.models import FloatField, Prefetch
from django.db.models.expressions import RawSQL
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsAdminRole
from rides.filters import RideFilter
from rides.models import Ride, RideEvent
from rides.serializers import (
    RideCreateSerializer,
    RideEventSerializer,
    RideListSerializer,
    RideUpdateSerializer,
)

# RideEvents are considered "today's" if created within this window.
TODAYS_EVENTS_WINDOW = timedelta(hours=24)
ALLOWED_ORDERING = {"pickup_time", "-pickup_time", "distance", "-distance"}


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                "ordering",
                OpenApiTypes.STR,
                description=(
                    "Sort order: pickup_time, -pickup_time, distance, -distance. "
                    "Distance ordering requires the lat and lng params."
                ),
            ),
            OpenApiParameter(
                "lat", OpenApiTypes.FLOAT, description="Target pickup latitude (distance sorting)."
            ),
            OpenApiParameter(
                "lng", OpenApiTypes.FLOAT, description="Target pickup longitude (distance sorting)."
            ),
        ]
    )
)
class RideViewSet(viewsets.ModelViewSet):
    """Admin-only CRUD for rides, with filtering, sorting and pagination.

    The list endpoint returns each ride with its related rider/driver and the
    ``todays_ride_events`` field, fetched in a fixed number of queries
    regardless of page size (rides+rider+driver, prefetched events, COUNT).
    """

    permission_classes = [IsAuthenticated, IsAdminRole]
    # Custom ordering is handled in get_queryset(), so the global OrderingFilter
    # is intentionally dropped here.
    filter_backends = [DjangoFilterBackend]
    filterset_class = RideFilter

    def get_serializer_class(self):
        if self.action == "create":
            return RideCreateSerializer
        if self.action in ("update", "partial_update"):
            return RideUpdateSerializer
        return RideListSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Ride.objects.none()

        cutoff = timezone.now() - TODAYS_EVENTS_WINDOW
        queryset = Ride.objects.select_related("rider", "driver").prefetch_related(
            Prefetch(
                "ride_events",
                queryset=RideEvent.objects.filter(created_at__gte=cutoff).order_by("-created_at"),
                to_attr="todays_events",
            )
        )
        return self._apply_ordering(queryset)

    def _apply_ordering(self, queryset):
        ordering = self.request.query_params.get("ordering", "-pickup_time")
        if ordering not in ALLOWED_ORDERING:
            raise ValidationError(
                {"ordering": f"Must be one of: {', '.join(sorted(ALLOWED_ORDERING))}."}
            )

        if ordering in ("distance", "-distance"):
            lat, lng = self._get_target_coordinates()
            # PostGIS KNN operator (<->): index-assisted nearest-neighbour ordering
            # via the GiST index on pickup_point. For geography, <-> returns meters.
            # Parameters are bound (no string interpolation), so this is injection-safe.
            queryset = queryset.annotate(
                distance=RawSQL(
                    "pickup_point <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography",
                    (lng, lat),
                    output_field=FloatField(),
                )
            )
            order_by = "distance" if ordering == "distance" else "-distance"
        else:
            order_by = ordering

        # id_ride tiebreaker keeps pagination deterministic across pages.
        return queryset.order_by(order_by, "id_ride")

    def _get_target_coordinates(self):
        params = self.request.query_params
        lat, lng = params.get("lat"), params.get("lng")
        if lat is None or lng is None:
            raise ValidationError(
                {"lat": "lat and lng query params are required when ordering by distance."}
            )
        try:
            lat, lng = float(lat), float(lng)
        except ValueError:
            raise ValidationError({"lat": "lat and lng must be valid numbers."}) from None
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            raise ValidationError({"lat": "lat must be in [-90, 90] and lng in [-180, 180]."})
        return lat, lng


class RideEventViewSet(viewsets.ModelViewSet):
    """Admin-only CRUD for ride events."""

    permission_classes = [IsAuthenticated, IsAdminRole]
    serializer_class = RideEventSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return RideEvent.objects.none()
        return RideEvent.objects.select_related("ride").order_by("-created_at")
