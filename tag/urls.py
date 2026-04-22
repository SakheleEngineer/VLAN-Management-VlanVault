"""
Author: Sakhele George Mndaweni
Created: 2026-01-29
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'vlan-activities', VlanActivityViewSet, basename='vlan-activities')
router.register(r"tags", TagViewSet, basename="tag")

urlpatterns = [
    # ✅ ViewSet routes
    path('', include(router.urls)),

    # ✅ Custom standalone endpoint
    path('get-tagdata/', GetTagDataAPIView.as_view(), name='get-tagdata'),
]

