"""Tests for the JWT authentication endpoints."""

import pytest
from django.urls import reverse
from rest_framework_simplejwt.tokens import AccessToken

from accounts.models import User
from common.factories import TEST_PASSWORD, UserFactory

pytestmark = pytest.mark.django_db


def test_login_returns_tokens_with_role_claim(api_client):
    user = UserFactory(role=User.Role.ADMIN)
    resp = api_client.post(
        reverse("token_obtain_pair"),
        {"email": user.email, "password": TEST_PASSWORD},
        format="json",
    )
    assert resp.status_code == 200
    assert "access" in resp.data and "refresh" in resp.data
    assert AccessToken(resp.data["access"])["role"] == User.Role.ADMIN


def test_login_wrong_password_returns_401(api_client):
    user = UserFactory()
    resp = api_client.post(
        reverse("token_obtain_pair"),
        {"email": user.email, "password": "wrong-password"},
        format="json",
    )
    assert resp.status_code == 401


def test_refresh_returns_new_access(api_client):
    user = UserFactory()
    obtain = api_client.post(
        reverse("token_obtain_pair"),
        {"email": user.email, "password": TEST_PASSWORD},
        format="json",
    )
    resp = api_client.post(
        reverse("token_refresh"), {"refresh": obtain.data["refresh"]}, format="json"
    )
    assert resp.status_code == 200
    assert "access" in resp.data


def test_bearer_token_grants_access(api_client):
    admin = UserFactory(role=User.Role.ADMIN)
    token = api_client.post(
        reverse("token_obtain_pair"),
        {"email": admin.email, "password": TEST_PASSWORD},
        format="json",
    ).data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    assert api_client.get(reverse("ride-list")).status_code == 200
