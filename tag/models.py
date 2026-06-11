"""
Author: Sakhele George Mndaweni
Created: 2026-01-29
"""
from django.db import models
from tag_set.models import * 
from simple_history.models import HistoricalRecords


class ConfigurationSettings(models.Model):
    product_name = models.CharField(max_length=100)
    service_name = models.CharField(max_length=100)
    configuration_type = models.CharField(max_length=100)
    delivery_type = models.CharField(max_length=100)
    def __str__(self):
        return self.product_name


class Tag(models.Model):
    vlan       = models.PositiveIntegerField()
    division   = models.CharField(max_length=200, blank=True)
    customer   = models.CharField(max_length=100, blank=True)
    name       = models.CharField(max_length=200, blank=True)
    access_hs  = models.CharField(max_length=255, blank=True)
    sector     = models.CharField(max_length=200, blank=True)
    usage      = models.CharField(max_length=200, blank=True)
    service    = models.CharField(max_length=50, blank=True)
    speed      = models.CharField(max_length=200, blank=True)
    circ_no    = models.CharField(max_length=200, blank=True)
    Service_id = models.CharField(max_length=200, blank=True)
    comment    = models.CharField(max_length=200, blank=True)
    vlan_range = models.ForeignKey(TagRange, on_delete=models.CASCADE)
    configuration_settings = models.ForeignKey(
        ConfigurationSettings,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tags"
    )

    history = HistoricalRecords()  

    def clean(self):
        if not (self.vlan_range.vlan_start <= self.vlan <= self.vlan_range.vlan_end):
            raise ValidationError("VLAN outside assigned range")

class VlanActivity(models.Model):
    LEVEL_CHOICES = [
        ('INFO', 'Info'),
        ('WARN', 'Warning'),
        ('ERROR', 'Error'),
    ]

    vlan = models.PositiveIntegerField()
    message = models.TextField()
    level = models.CharField(max_length=5, choices=LEVEL_CHOICES, default='INFO')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.level}] VLAN {self.vlan_id}: {self.message}"


