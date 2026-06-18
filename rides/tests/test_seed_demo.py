"""Tests for the seed_demo management command."""

import pytest
from django.core.management import call_command

from accounts.models import User
from rides.models import Ride, RideEvent

pytestmark = pytest.mark.django_db


def test_seed_demo_creates_data_and_known_users():
    call_command("seed_demo", rides=5)
    assert Ride.objects.count() == 5
    assert RideEvent.objects.count() == 10  # one pickup + one dropoff per ride
    admin = User.objects.get(email="admin@example.com")
    assert admin.role == User.Role.ADMIN and admin.check_password("AdminPass123")
    rider = User.objects.get(email="rider@example.com")
    assert rider.role == User.Role.RIDER and rider.check_password("RiderPass123")


def test_seed_demo_is_idempotent():
    call_command("seed_demo", rides=5)
    call_command("seed_demo", rides=5)  # no --flush -> should be a no-op
    assert Ride.objects.count() == 5


def test_seed_demo_flush_reseeds():
    call_command("seed_demo", rides=5)
    call_command("seed_demo", rides=3, flush=True)
    assert Ride.objects.count() == 3
