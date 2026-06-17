"""Serializers for the rides app."""

from datetime import timedelta

from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from accounts.models import User
from accounts.serializers import UserSerializer
from common.serializers import StrictFieldsModelSerializer
from rides.models import Ride, RideEvent


class RideEventSerializer(StrictFieldsModelSerializer):
    """Serializer for ride events (used both nested and standalone)."""

    id_ride = serializers.PrimaryKeyRelatedField(source="ride", queryset=Ride.objects.all())

    class Meta:
        model = RideEvent
        fields = ["id_ride_event", "id_ride", "description", "created_at"]
        read_only_fields = ["id_ride_event"]


class RideListSerializer(serializers.ModelSerializer):
    """Read serializer for the Ride list/detail endpoints.

    Exposes the related rider/driver both as ids and nested objects, plus
    ``todays_ride_events`` (events from the last 24h) read from the prefetched
    ``todays_events`` attribute set by the ViewSet queryset.
    """

    id_rider = serializers.IntegerField(source="rider_id", read_only=True)
    id_driver = serializers.IntegerField(source="driver_id", read_only=True)
    rider = UserSerializer(read_only=True)
    driver = UserSerializer(read_only=True)
    todays_ride_events = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()

    class Meta:
        model = Ride
        fields = [
            "id_ride",
            "status",
            "id_rider",
            "id_driver",
            "rider",
            "driver",
            "pickup_latitude",
            "pickup_longitude",
            "dropoff_latitude",
            "dropoff_longitude",
            "pickup_time",
            "todays_ride_events",
            "distance",
        ]

    @extend_schema_field(RideEventSerializer(many=True))
    def get_todays_ride_events(self, obj):
        # Prefer the prefetched, already-filtered events (set by the ViewSet via
        # Prefetch(to_attr="todays_events")). Fall back to a filtered query so
        # the serializer is correct outside the optimized list path; in neither
        # case is the full RideEvent set loaded.
        events = getattr(obj, "todays_events", None)
        if events is None:
            cutoff = timezone.now() - timedelta(hours=24)
            events = obj.ride_events.filter(created_at__gte=cutoff)
        return RideEventSerializer(events, many=True).data

    @extend_schema_field(serializers.FloatField(allow_null=True))
    def get_distance(self, obj):
        # Populated only when the queryset is annotated with a PostGIS Distance
        # (i.e. when sorting by distance); meters, or null otherwise.
        distance = getattr(obj, "distance", None)
        return distance.m if distance is not None else None


class RideWriteSerializer(StrictFieldsModelSerializer):
    """Base write serializer for rides.

    ``Ride.save()`` keeps ``pickup_point`` in sync with the coordinates, so no
    spatial logic lives here.
    """

    id_rider = serializers.PrimaryKeyRelatedField(source="rider", queryset=User.objects.all())
    id_driver = serializers.PrimaryKeyRelatedField(source="driver", queryset=User.objects.all())

    class Meta:
        model = Ride
        fields = [
            "id_ride",
            "status",
            "id_rider",
            "id_driver",
            "pickup_latitude",
            "pickup_longitude",
            "dropoff_latitude",
            "dropoff_longitude",
            "pickup_time",
        ]
        read_only_fields = ["id_ride"]

    def validate(self, attrs):
        for field in ("pickup_latitude", "dropoff_latitude"):
            value = attrs.get(field)
            if value is not None and not -90 <= value <= 90:
                raise serializers.ValidationError({field: "Latitude must be between -90 and 90."})
        for field in ("pickup_longitude", "dropoff_longitude"):
            value = attrs.get(field)
            if value is not None and not -180 <= value <= 180:
                raise serializers.ValidationError(
                    {field: "Longitude must be between -180 and 180."}
                )
        return attrs


class RideCreateSerializer(RideWriteSerializer):
    """Create serializer for rides."""


class RideUpdateSerializer(RideWriteSerializer):
    """Update serializer for rides."""
