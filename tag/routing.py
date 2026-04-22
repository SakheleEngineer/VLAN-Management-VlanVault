
"""
Author: Sakhele George Mndaweni
Created: 2026-01-29
"""
from django.urls import re_path
from .consumers import VlanConsumer

websocket_urlpatterns = [
    re_path("ws/vlan-logs/", VlanConsumer.as_asgi()),
]
