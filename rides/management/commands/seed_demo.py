"""Seed the database with realistic demo data for local exploration / the demo.

Creates two known login users (an admin and a non-admin), a pool of riders and
drivers, and a configurable number of rides with pickup/dropoff events. Designed
to be safe to run repeatedly: it is a no-op when rides already exist unless
``--flush`` is passed.

Usage:
    python manage.py seed_demo                 # ~500 rides (skips if data exists)
    python manage.py seed_demo --rides 2000    # custom volume
    python manage.py seed_demo --flush         # wipe demo data and re-seed
"""

import random
from datetime import timedelta

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone

from accounts.models import User
from rides.models import Ride, RideEvent

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "AdminPass123"
NON_ADMIN_EMAIL = "rider@example.com"
NON_ADMIN_PASSWORD = "RiderPass123"

# City centres (lat, lng) used as anchors; each ride jitters around one of these.
CITIES = [
    (37.7749, -122.4194),  # San Francisco
    (40.7128, -74.0060),  # New York
    (34.0522, -118.2437),  # Los Angeles
    (41.8781, -87.6298),  # Chicago
]
DRIVER_NAMES = [
    ("Chris", "Hemsworth"),
    ("Howard", "Young"),
    ("Randy", "Watson"),
    ("Maria", "Garcia"),
    ("Liam", "Nguyen"),
    ("Sofia", "Rossi"),
    ("Noah", "Kim"),
    ("Emma", "Silva"),
]
RIDER_LAST_NAMES = [
    "Doe",
    "Smith",
    "Brown",
    "Lee",
    "Costa",
    "Khan",
    "Müller",
    "Tanaka",
    "Lopez",
    "Ivanov",
]


class Command(BaseCommand):
    help = "Seed the database with demo users, rides and ride events."

    def add_arguments(self, parser):
        parser.add_argument("--rides", type=int, default=500, help="Number of rides to create.")
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing rides/events and demo users before seeding.",
        )

    def handle(self, *args, **options):
        ride_count = options["rides"]
        flush = options["flush"]

        if flush:
            RideEvent.objects.all().delete()
            Ride.objects.all().delete()

        if Ride.objects.exists() and not flush:
            self.stdout.write(
                self.style.WARNING(
                    f"Rides already exist ({Ride.objects.count()}); use --flush to re-seed."
                )
            )
            return

        admin, riders, drivers = self._ensure_users()
        self._create_rides(ride_count, riders, drivers)

        with connection.cursor() as cursor:
            cursor.execute("ANALYZE rides;")
            cursor.execute("ANALYZE ride_events;")

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {Ride.objects.count()} rides, {RideEvent.objects.count()} events, "
                f"{User.objects.count()} users.\n"
                f"  admin login:     {ADMIN_EMAIL} / {ADMIN_PASSWORD}\n"
                f"  non-admin login: {NON_ADMIN_EMAIL} / {NON_ADMIN_PASSWORD}"
            )
        )

    def _ensure_users(self):
        admin, _ = User.objects.get_or_create(
            email=ADMIN_EMAIL,
            defaults={
                "first_name": "Ada",
                "last_name": "Min",
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin.set_password(ADMIN_PASSWORD)
        admin.save()

        non_admin, _ = User.objects.get_or_create(
            email=NON_ADMIN_EMAIL,
            defaults={"first_name": "Ria", "last_name": "Der", "role": User.Role.RIDER},
        )
        non_admin.set_password(NON_ADMIN_PASSWORD)
        non_admin.save()

        riders = [non_admin]
        for i, last in enumerate(RIDER_LAST_NAMES):
            rider, _ = User.objects.get_or_create(
                email=f"rider{i}@example.com",
                defaults={"first_name": f"Rider{i}", "last_name": last, "role": User.Role.RIDER},
            )
            riders.append(rider)

        drivers = []
        for i, (first, last) in enumerate(DRIVER_NAMES):
            driver, _ = User.objects.get_or_create(
                email=f"driver{i}@example.com",
                defaults={"first_name": first, "last_name": last, "role": User.Role.DRIVER},
            )
            drivers.append(driver)

        return admin, riders, drivers

    def _create_rides(self, ride_count, riders, drivers):
        now = timezone.now()
        statuses = [c[0] for c in Ride.Status.choices]
        rides = []
        # pickup_time offsets in minutes: the first ~20 rides are within the last
        # 24h (so todays_ride_events is populated on page 1), the rest spread over
        # ~120 days.
        recent = min(20, ride_count)
        for i in range(ride_count):
            lat0, lng0 = random.choice(CITIES)
            lat = lat0 + random.uniform(-0.1, 0.1)
            lng = lng0 + random.uniform(-0.1, 0.1)
            if i < recent:
                pickup_time = now - timedelta(minutes=random.randint(5, 23 * 60))
            else:
                pickup_time = now - timedelta(minutes=random.randint(24 * 60, 120 * 24 * 60))
            rides.append(
                Ride(
                    status=random.choice(statuses),
                    rider=random.choice(riders),
                    driver=random.choice(drivers),
                    pickup_latitude=lat,
                    pickup_longitude=lng,
                    dropoff_latitude=lat + random.uniform(-0.1, 0.1),
                    dropoff_longitude=lng + random.uniform(-0.1, 0.1),
                    pickup_time=pickup_time,
                    pickup_point=Point(lng, lat, srid=4326),
                )
            )
        created = Ride.objects.bulk_create(rides)

        events = []
        for ride in created:
            duration = timedelta(minutes=random.randint(10, 150))  # some > 1h for the bonus report
            events.append(
                RideEvent(
                    ride=ride, description="Status changed to pickup", created_at=ride.pickup_time
                )
            )
            events.append(
                RideEvent(
                    ride=ride,
                    description="Status changed to dropoff",
                    created_at=ride.pickup_time + duration,
                )
            )
        RideEvent.objects.bulk_create(events)
