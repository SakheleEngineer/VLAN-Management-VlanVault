from rest_framework.routers import DefaultRouter
from .views import DataCenterViewSet

router = DefaultRouter()
router.register(r'datacenters', DataCenterViewSet,basename = "datacenter")

urlpatterns = router.urls
