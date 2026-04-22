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
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        null=True,
        blank=True
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

    def save(self, *args, **kwargs):
        user = getattr(self, '_current_user', None)
        if user and not user.is_superuser and self.group not in user.groups.all():
            raise ValidationError("You cannot create or modify a range for this group.")
        super().save(*args, **kwargs)


    def clean(self):
        
            if self.vlan_start >= self.vlan_end:
                raise ValidationError("vlan_start must be less than vlan_end")

            if self.vlan_start <= 0 or self.vlan_end > 4094:
                raise ValidationError("vlan_start must be not be less than 0 and  vlan_end must be less 4095")
            

            stags_qs = self.stags.all() if self.pk else getattr(self, '_stags_temp', [])

            base_qs = TagRange.objects.filter(
                company=self.company,
                datacenter=self.datacenter
            ).exclude(pk=self.pk)

            if stags_qs:
                overlapping = base_qs.filter(stags__in=stags_qs).distinct()
            else:
                overlapping = base_qs.filter(stags__isnull=True)

            for other in overlapping:
                if self.vlan_start <= other.vlan_end and self.vlan_end >= other.vlan_start:
                    stag_names = ", ".join([s.name for s in stags_qs]) if stags_qs else "No STags"
                    raise ValidationError(
                        f"VLAN range overlaps with '{other.name}' in the same datacenter "
                        f"for the same company and STag(s): {stag_names}."
                    )

            #Check group permissions
            user = getattr(self, '_current_user', None)
            if user and not user.is_superuser and self.vlan_range.group not in user.groups.all():
                raise ValidationError("You cannot create or modify a VLAN in this range")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.vlan_start}-{self.vlan_end})"
