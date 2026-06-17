"""Shared pytest fixtures."""

import pytest
from rest_framework.test import APIClient

from accounts.models import User
from common.factories import UserFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return UserFactory(role=User.Role.ADMIN)


@pytest.fixture
def rider_user(db):
    return UserFactory(role=User.Role.RIDER)


@pytest.fixture
def driver_user(db):
    return UserFactory(role=User.Role.DRIVER)


@pytest.fixture
def admin_client(admin_user):
    """A dedicated APIClient authenticated as an admin user."""
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def rider_client(rider_user):
    """A dedicated APIClient authenticated as a non-admin (rider) user.

    Each authenticated client is a separate instance so the anonymous
    ``api_client`` is never accidentally authenticated within the same test.
    """
    client = APIClient()
    client.force_authenticate(user=rider_user)
    return client
