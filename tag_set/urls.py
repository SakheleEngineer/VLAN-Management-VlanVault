# urls.py
from rest_framework.routers import DefaultRouter
from rest_framework.routers import DefaultRouter
from .views import TagRangeViewSet, STagViewSet

router = DefaultRouter()
router.register(r"tagranges", TagRangeViewSet, basename="tagrange")
router.register(r"stags", STagViewSet, basename="stag")

urlpatterns = router.urls
