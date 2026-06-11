"""
Author: Sakhle Mndaweni
Created: 2025-12-15
Description:
    Data models for Tag management.
"""
from django.db import models
from django.core.exceptions import ValidationError
from data_center.models import *
from company.models import *
import uuid
from django.db.models import Q
from django.contrib.auth.models import Group

class STag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class TagRange(models.Model):

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    name = models.CharField(max_length=100)
    vlan_start = models.PositiveIntegerField()
    vlan_end = models.PositiveIntegerField()
    groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name="tag_ranges"
    )

    datacenter = models.ForeignKey(
        DataCenter,
        related_name="tag_ranges",
        on_delete=models.CASCADE,
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
    )

    stags = models.ManyToManyField(
        STag,
        related_name="tag_ranges",
        blank=True,
    )

    def user_has_access(self, user):
        return self.groups.filter(
            id__in=user.groups.values_list(
                "id",
                flat=True
            )
        ).exists()

    def __str__(self):
        return f"{self.name} ({self.vlan_start}-{self.vlan_end})"
