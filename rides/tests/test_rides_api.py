"""Tests for the rides API (authorization, list shape, filtering, sorting, pagination)."""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from common.factories import RideEventFactory, RideFactory, UserFactory
from rides.models import Ride

pytestmark = pytest.mark.django_db


def _ride_payload(rider, driver, **overrides):
    data = {
        "status": Ride.Status.PICKUP,
        "id_rider": rider.pk,
        "id_driver": driver.pk,
        "pickup_latitude": 37.77,
        "pickup_longitude": -122.41,
        "dropoff_latitude": 37.8,
        "dropoff_longitude": -122.4,
        "pickup_time": timezone.now().isoformat(),
    }
    data.update(overrides)
    return data


class TestRidesAuthorization:
    def test_list(self, api_client, rider_client, admin_client):
        url = reverse("ride-list")
        assert api_client.get(url).status_code == 401
        assert rider_client.get(url).status_code == 403
        assert admin_client.get(url).status_code == 200

    def test_retrieve(self, api_client, rider_client, admin_client):
        ride = RideFactory()
        url = reverse("ride-detail", args=[ride.pk])
        assert api_client.get(url).status_code == 401
        assert rider_client.get(url).status_code == 403
        assert admin_client.get(url).status_code == 200

    def test_create(self, api_client, rider_client, admin_client, rider_user, driver_user):
        url = reverse("ride-list")
        payload = _ride_payload(rider_user, driver_user)
        assert api_client.post(url, payload, format="json").status_code == 401
        assert rider_client.post(url, payload, format="json").status_code == 403
        assert admin_client.post(url, payload, format="json").status_code == 201

    def test_update(self, api_client, rider_client, admin_client):
        ride = RideFactory()
        url = reverse("ride-detail", args=[ride.pk])
        body = {"status": Ride.Status.DROPOFF}
        assert api_client.patch(url, body, format="json").status_code == 401
        assert rider_client.patch(url, body, format="json").status_code == 403
        assert admin_client.patch(url, body, format="json").status_code == 200

    def test_delete(self, api_client, rider_client, admin_client):
        ride = RideFactory()
        url = reverse("ride-detail", args=[ride.pk])
        assert api_client.delete(url).status_code == 401
        assert rider_client.delete(url).status_code == 403
        assert admin_client.delete(url).status_code == 204


class TestRideListShape:
    def test_nested_ids_and_todays_events(self, admin_client):
        ride = RideFactory()
        RideEventFactory(ride=ride, description="Status changed to pickup")
        RideEventFactory(
            ride=ride, description="Old", created_at=timezone.now() - timedelta(hours=48)
        )
        resp = admin_client.get(reverse("ride-list"))
        assert resp.status_code == 200
        result = resp.data["results"][0]
        assert result["id_rider"] == ride.rider_id
        assert result["id_driver"] == ride.driver_id
        assert result["rider"]["email"] == ride.rider.email
        assert result["driver"]["email"] == ride.driver.email
        descriptions = [event["description"] for event in result["todays_ride_events"]]
        assert descriptions == ["Status changed to pickup"]


class TestRideFiltering:
    def test_filter_by_status(self, admin_client):
        RideFactory(status=Ride.Status.PICKUP)
        RideFactory(status=Ride.Status.DROPOFF)
        resp = admin_client.get(reverse("ride-list"), {"status": Ride.Status.DROPOFF})
        assert resp.data["count"] == 1
        assert resp.data["results"][0]["status"] == Ride.Status.DROPOFF

    def test_filter_by_rider_email(self, admin_client):
        target = UserFactory(role=User.Role.RIDER, email="target@example.com")
        RideFactory(rider=target)
        RideFactory()
        resp = admin_client.get(reverse("ride-list"), {"rider_email": "target@example.com"})
        assert resp.data["count"] == 1


class TestRideSorting:
    def test_sort_by_pickup_time(self, admin_client):
        now = timezone.now()
        RideFactory(pickup_time=now - timedelta(hours=2))
        RideFactory(pickup_time=now)
        resp = admin_client.get(reverse("ride-list"), {"ordering": "pickup_time"})
        times = [r["pickup_time"] for r in resp.data["results"]]
        assert times == sorted(times)

    def test_sort_by_distance(self, admin_client):
        near = RideFactory(pickup_latitude=37.77, pickup_longitude=-122.41)
        RideFactory(pickup_latitude=40.71, pickup_longitude=-74.0)
        resp = admin_client.get(
            reverse("ride-list"), {"ordering": "distance", "lat": "37.77", "lng": "-122.41"}
        )
        results = resp.data["results"]
        assert results[0]["id_ride"] == near.pk
        distances = [r["distance"] for r in results]
        assert distances == sorted(distances)

    def test_distance_without_coordinates_returns_400(self, admin_client):
        assert admin_client.get(reverse("ride-list"), {"ordering": "distance"}).status_code == 400

    def test_invalid_ordering_returns_400(self, admin_client):
        assert admin_client.get(reverse("ride-list"), {"ordering": "bogus"}).status_code == 400


class TestRidePagination:
    def test_page_size_and_navigation(self, admin_client):
        RideFactory.create_batch(3)
        resp = admin_client.get(reverse("ride-list"), {"page_size": 1})
        assert resp.data["count"] == 3
        assert len(resp.data["results"]) == 1
        assert resp.data["next"] is not None
        page2 = admin_client.get(reverse("ride-list"), {"page_size": 1, "page": 2})
        assert page2.status_code == 200
