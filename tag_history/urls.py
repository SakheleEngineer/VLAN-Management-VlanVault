from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HistoryViewSet, tag_history_view

router = DefaultRouter()
router.register(r"history", HistoryViewSet, basename="history")

urlpatterns = [
    path("", include(router.urls)),
    path('tags/history/<int:tag_id>/', tag_history_view, name='tag-history'),
]