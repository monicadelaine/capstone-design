from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import SponsorViewSet, StudentViewSet, profile_view

app_name = "user"

router = DefaultRouter()

# For viewsets
router.register(r"sponsors", SponsorViewSet, basename="sponsor")
router.register(r"students", StudentViewSet, basename="student")

urlpatterns = [
    path("", include(router.urls)),
    path("profile/", profile_view, name="profile"),
]
