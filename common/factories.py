"""factory_boy factories for tests (dev-only; never imported by runtime code)."""

import factory
from django.utils import timezone

from accounts.models import User
from rides.models import Ride, RideEvent

TEST_PASSWORD = "password123"


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    role = User.Role.RIDER
    first_name = factory.Sequence(lambda n: f"First{n}")
    last_name = "User"
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    phone_number = "+10000000000"
    password = factory.django.Password(TEST_PASSWORD)


class RideFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Ride

    status = Ride.Status.PICKUP
    rider = factory.SubFactory(UserFactory, role=User.Role.RIDER)
    driver = factory.SubFactory(UserFactory, role=User.Role.DRIVER)
    pickup_latitude = 37.7749
    pickup_longitude = -122.4194
    dropoff_latitude = 37.8044
    dropoff_longitude = -122.2712
    pickup_time = factory.LazyFunction(timezone.now)


class RideEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RideEvent

    ride = factory.SubFactory(RideFactory)
    description = "Status changed to pickup"
    created_at = factory.LazyFunction(timezone.now)
