"""Tests for the users API (authorization + behavior)."""

import pytest
from django.urls import reverse

from accounts.models import User

pytestmark = pytest.mark.django_db


def _user_payload(**overrides):
    data = {
        "email": "new@example.com",
        "password": "Secret12345",
        "first_name": "New",
        "last_name": "User",
        "role": User.Role.RIDER,
    }
    data.update(overrides)
    return data


class TestUsersAuthorization:
    def test_list(self, api_client, rider_client, admin_client):
        url = reverse("user-list")
        assert api_client.get(url).status_code == 401
        assert rider_client.get(url).status_code == 403
        assert admin_client.get(url).status_code == 200

    def test_retrieve(self, api_client, rider_client, admin_client, rider_user):
        url = reverse("user-detail", args=[rider_user.pk])
        assert api_client.get(url).status_code == 401
        assert rider_client.get(url).status_code == 403
        assert admin_client.get(url).status_code == 200

    def test_create(self, api_client, rider_client, admin_client):
        url = reverse("user-list")
        assert api_client.post(url, _user_payload(), format="json").status_code == 401
        assert rider_client.post(url, _user_payload(), format="json").status_code == 403
        assert admin_client.post(url, _user_payload(), format="json").status_code == 201

    def test_update(self, api_client, rider_client, admin_client, rider_user):
        url = reverse("user-detail", args=[rider_user.pk])
        body = {"first_name": "Changed"}
        assert api_client.patch(url, body, format="json").status_code == 401
        assert rider_client.patch(url, body, format="json").status_code == 403
        assert admin_client.patch(url, body, format="json").status_code == 200

    def test_delete(self, api_client, rider_client, admin_client, rider_user):
        url = reverse("user-detail", args=[rider_user.pk])
        assert api_client.delete(url).status_code == 401
        assert rider_client.delete(url).status_code == 403
        assert admin_client.delete(url).status_code == 204


class TestUsersBehavior:
    def test_create_hashes_password(self, admin_client):
        resp = admin_client.post(
            reverse("user-list"), _user_payload(email="hash@example.com"), format="json"
        )
        assert resp.status_code == 201
        assert "password" not in resp.data
        assert User.objects.get(email="hash@example.com").check_password("Secret12345")

    def test_create_rejects_unknown_field(self, admin_client):
        resp = admin_client.post(
            reverse("user-list"), _user_payload(is_superuser=True), format="json"
        )
        assert resp.status_code == 400
        assert "is_superuser" in resp.data
