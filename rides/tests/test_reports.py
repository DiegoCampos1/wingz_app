"""Tests for the bonus reporting SQL (trips longer than one hour)."""

import json
from datetime import UTC, datetime, timedelta
from io import StringIO

import pytest
from django.conf import settings
from django.core.management import call_command
from django.db import connection

from accounts.models import User
from common.factories import RideEventFactory, RideFactory, UserFactory

pytestmark = pytest.mark.django_db

SQL_PATH = settings.BASE_DIR / "reports" / "trips_over_one_hour.sql"


def _trip(driver, rider, pickup_at, duration_minutes):
    ride = RideFactory(driver=driver, rider=rider, pickup_time=pickup_at)
    RideEventFactory(ride=ride, description="Status changed to pickup", created_at=pickup_at)
    RideEventFactory(
        ride=ride,
        description="Status changed to dropoff",
        created_at=pickup_at + timedelta(minutes=duration_minutes),
    )
    return ride


@pytest.fixture
def report_data():
    driver = UserFactory(role=User.Role.DRIVER, first_name="Chris", last_name="Hemsworth")
    rider = UserFactory(role=User.Role.RIDER)
    _trip(driver, rider, datetime(2024, 1, 5, 10, 0, tzinfo=UTC), 90)
    _trip(driver, rider, datetime(2024, 1, 10, 9, 0, tzinfo=UTC), 90)
    _trip(driver, rider, datetime(2024, 1, 15, 8, 0, tzinfo=UTC), 30)  # < 1h, excluded
    _trip(driver, rider, datetime(2024, 2, 3, 14, 0, tzinfo=UTC), 120)


def test_report_sql_counts_trips_over_one_hour(report_data):
    with connection.cursor() as cursor:
        cursor.execute(SQL_PATH.read_text())
        rows = cursor.fetchall()
    # The 30-minute January trip is excluded; results are ordered by month, driver.
    assert rows == [("2024-01", "Chris H", 2), ("2024-02", "Chris H", 1)]


def test_report_management_command_writes_json(report_data, tmp_path):
    out = StringIO()
    call_command("trips_over_one_hour", stdout=out, output_dir=str(tmp_path))
    output = out.getvalue()
    assert "Chris H" in output and "2024-01" in output and "2024-02" in output

    files = list(tmp_path.glob("trips_over_one_hour_*.json"))
    assert len(files) == 1
    payload = json.loads(files[0].read_text())
    assert payload["count"] == 2
    assert {"month": "2024-01", "driver": "Chris H", "trips_over_one_hour": 2} in payload["rows"]
