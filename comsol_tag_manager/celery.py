import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "comsol_tag_manager.settings")

app = Celery("comsol_tag_manager")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

app.conf.timezone = "Africa/Johannesburg"
