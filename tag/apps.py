"""
Author: Sakhele George Mndaweni
Created: 2026-01-29
"""
from django.apps import AppConfig


class TagConfig(AppConfig):
    name = 'tag'
    def ready(self):
        import tag.signals


class ActivityConfig(AppConfig):
    name = 'Activity'
    def ready(self):
        import tag.signals