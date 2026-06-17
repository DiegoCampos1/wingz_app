"""Filters for the rides app."""

import django_filters as filters

from rides.models import Ride


class RideFilter(filters.FilterSet):
    """Filter rides by status and by rider email."""

    status = filters.ChoiceFilter(choices=Ride.Status.choices)
    rider_email = filters.CharFilter(field_name="rider__email", lookup_expr="iexact")

    class Meta:
        model = Ride
        fields = ["status", "rider_email"]
