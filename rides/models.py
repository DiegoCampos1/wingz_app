"""Domain models for rides.

``Ride`` carries a derived PostGIS ``pickup_point`` (kept in sync from the
plain latitude/longitude fields) so the Ride List API can sort by distance to
a given GPS location efficiently using a GiST spatial index. ``RideEvent``
records status-change events; its composite ``(ride, created_at)`` index makes
the "events from the last 24h" lookup cheap on a large table.
"""

from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.utils import timezone

from accounts.models import User


class Ride(models.Model):
    """A ride between a rider and a driver."""

    class Status(models.TextChoices):
        EN_ROUTE = "en-route", "En route"
        PICKUP = "pickup", "Pickup"
        DROPOFF = "dropoff", "Dropoff"

    id_ride = models.BigAutoField(primary_key=True)
    status = models.CharField(max_length=20, choices=Status.choices)
    rider = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        db_column="id_rider",
        related_name="rides_as_rider",
    )
    driver = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        db_column="id_driver",
        related_name="rides_as_driver",
    )
    pickup_latitude = models.FloatField()
    pickup_longitude = models.FloatField()
    dropoff_latitude = models.FloatField()
    dropoff_longitude = models.FloatField()
    pickup_time = models.DateTimeField()
    # Derived geography point used for efficient distance (KNN) sorting. Kept in
    # sync from pickup_longitude/pickup_latitude in save(); nullable so rows
    # created by bulk/raw loads can be filled later via backfill_pickup_points.
    pickup_point = models.PointField(
        geography=True,
        srid=4326,
        null=True,
        blank=True,
        spatial_index=True,
    )

    class Meta:
        db_table = "rides"
        indexes = [
            models.Index(fields=["pickup_time"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Ride #{self.pk} ({self.status})"

    def save(self, *args, **kwargs):
        # Keep the spatial point in sync with the source coordinates.
        if self.pickup_latitude is not None and self.pickup_longitude is not None:
            self.pickup_point = Point(self.pickup_longitude, self.pickup_latitude, srid=4326)
        super().save(*args, **kwargs)


class RideEvent(models.Model):
    """A status-change event that occurred during a ride."""

    id_ride_event = models.BigAutoField(primary_key=True)
    ride = models.ForeignKey(
        Ride,
        on_delete=models.CASCADE,
        db_column="id_ride",
        related_name="ride_events",
    )
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "ride_events"
        indexes = [
            models.Index(fields=["ride", "created_at"]),
        ]

    def __str__(self):
        return f"RideEvent #{self.pk} for Ride #{self.ride_id}"
