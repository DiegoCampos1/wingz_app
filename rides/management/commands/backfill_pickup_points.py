"""Backfill Ride.pickup_point from the latitude/longitude columns.

Useful for rows inserted via bulk_create or raw SQL, which bypass
``Ride.save()`` and therefore never populate the derived spatial point.
"""

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from rides.models import Ride


class Command(BaseCommand):
    help = "Populate Ride.pickup_point from pickup_longitude/pickup_latitude where missing."

    def handle(self, *args, **options):
        updated = 0
        queryset = Ride.objects.filter(pickup_point__isnull=True)
        for ride in queryset.iterator():
            if ride.pickup_latitude is not None and ride.pickup_longitude is not None:
                ride.pickup_point = Point(ride.pickup_longitude, ride.pickup_latitude, srid=4326)
                ride.save(update_fields=["pickup_point"])
                updated += 1
        self.stdout.write(self.style.SUCCESS(f"Backfilled {updated} ride(s)."))
