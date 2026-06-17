"""Regression test for the Ride List query budget (2 data queries + 1 COUNT)."""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from common.factories import RideEventFactory, RideFactory

pytestmark = pytest.mark.django_db


def test_ride_list_uses_three_queries(admin_client, django_assert_num_queries):
    # Several rides, each with recent + old events: the query count must stay
    # constant (no N+1) regardless of how many rides/events exist.
    now = timezone.now()
    for _ in range(5):
        ride = RideFactory()
        RideEventFactory(ride=ride, created_at=now)
        RideEventFactory(ride=ride, created_at=now - timedelta(hours=48))

    with django_assert_num_queries(3):
        resp = admin_client.get(reverse("ride-list"))
        assert resp.status_code == 200
    assert resp.data["count"] == 5
