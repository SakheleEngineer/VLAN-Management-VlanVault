
from django.db import models
from django.core.exceptions import ValidationError
from region.views import *

class DataCenter(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    region = models.CharField(max_length=255)

    def __str__(self):
        return self.name

