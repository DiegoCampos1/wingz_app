"""Root URL configuration for the Wingz Ride Management API."""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import AdminTokenObtainPairView, UserViewSet
from config.views import health
from rides.views import RideEventViewSet, RideViewSet

router = DefaultRouter()
router.register("rides", RideViewSet, basename="ride")
router.register("ride-events", RideEventViewSet, basename="rideevent")
router.register("users", UserViewSet, basename="user")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/auth/token/", AdminTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("api/", include(router.urls)),
]
