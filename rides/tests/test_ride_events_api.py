"""Tests for the ride-events API (authorization + CRUD)."""

import pytest
from django.urls import reverse

from common.factories import RideEventFactory, RideFactory

pytestmark = pytest.mark.django_db


class TestRideEventsAuthorization:
    def test_list(self, api_client, rider_client, admin_client):
        url = reverse("rideevent-list")
        assert api_client.get(url).status_code == 401
        assert rider_client.get(url).status_code == 403
        assert admin_client.get(url).status_code == 200

    def test_retrieve(self, api_client, rider_client, admin_client):
        event = RideEventFactory()
        url = reverse("rideevent-detail", args=[event.pk])
        assert api_client.get(url).status_code == 401
        assert rider_client.get(url).status_code == 403
        assert admin_client.get(url).status_code == 200

    def test_create(self, api_client, rider_client, admin_client):
        ride = RideFactory()
        url = reverse("rideevent-list")
        payload = {"id_ride": ride.pk, "description": "Status changed to pickup"}
        assert api_client.post(url, payload, format="json").status_code == 401
        assert rider_client.post(url, payload, format="json").status_code == 403
        assert admin_client.post(url, payload, format="json").status_code == 201

    def test_update(self, api_client, rider_client, admin_client):
        event = RideEventFactory()
        url = reverse("rideevent-detail", args=[event.pk])
        body = {"description": "Updated description"}
        assert api_client.patch(url, body, format="json").status_code == 401
        assert rider_client.patch(url, body, format="json").status_code == 403
        assert admin_client.patch(url, body, format="json").status_code == 200

    def test_delete(self, api_client, rider_client, admin_client):
        event = RideEventFactory()
        url = reverse("rideevent-detail", args=[event.pk])
        assert api_client.delete(url).status_code == 401
        assert rider_client.delete(url).status_code == 403
        assert admin_client.delete(url).status_code == 204
