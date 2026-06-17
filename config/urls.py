"""Root URL configuration for the Wingz Ride Management API.

Only foundation routes are wired here. Business endpoints (users, rides,
ride-events) and the JWT auth routes are added in later commits.
"""

from django.contrib import admin
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from config.views import health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]
