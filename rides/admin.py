"""Admin configuration for the ride domain models (aids manual inspection)."""

from django.contrib import admin

from rides.models import Ride, RideEvent


@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = ("id_ride", "status", "rider", "driver", "pickup_time")
    list_filter = ("status",)
    search_fields = ("rider__email", "driver__email")
    # pickup_point is derived from the coordinates in Ride.save(); hide it from
    # the form so it is never edited by hand.
    exclude = ("pickup_point",)


@admin.register(RideEvent)
class RideEventAdmin(admin.ModelAdmin):
    list_display = ("id_ride_event", "ride", "description", "created_at")
    search_fields = ("description",)
