# urls.py
from rest_framework.routers import DefaultRouter
from .views import RegionViewSet

router = DefaultRouter()
router.register(r"regions", RegionViewSet, basename="region")

urlpatterns = router.urls
