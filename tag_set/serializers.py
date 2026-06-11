# serializers.py
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from .models import *


class TagRangeSerializer(serializers.ModelSerializer):
    stags = serializers.PrimaryKeyRelatedField(
        queryset=STag.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = TagRange
        fields = "__all__"

    def validate(self, attrs):
        request = self.context.get("request")
        user = request.user if request else None

        # Get current instance for updates
        instance = getattr(self, "instance", None)

        # Values for create/update
        company = attrs.get(
            "company",
            instance.company if instance else None
        )

        datacenter = attrs.get(
            "datacenter",
            instance.datacenter if instance else None
        )

        vlan_start = attrs.get(
            "vlan_start",
            instance.vlan_start if instance else None
        )

        vlan_end = attrs.get(
            "vlan_end",
            instance.vlan_end if instance else None
        )

        stags = attrs.get(
            "stags",
            instance.stags.all() if instance else []
        )

        # -------------------------
        # VLAN range validation
        # -------------------------
        if vlan_start >= vlan_end:
            raise serializers.ValidationError(
                {
                    "vlan_start":
                    "vlan_start must be less than vlan_end"
                }
            )

        if vlan_start <= 0 or vlan_end > 4094:
            raise serializers.ValidationError(
                {
                    "vlan_start":
                    "vlan_start must not be less than 0",
                    "vlan_end":
                    "vlan_end must be less than 4095"
                }
            )

        # -------------------------
        # Overlap validation
        # -------------------------
        base_qs = TagRange.objects.filter(
            company=company,
            datacenter=datacenter
        )

        if instance:
            base_qs = base_qs.exclude(
                pk=instance.pk
            )

        if stags:
            overlapping = base_qs.filter(
                stags__in=stags
            ).distinct()
        else:
            overlapping = base_qs.filter(
                stags__isnull=True
            )

        for other in overlapping:
            if (
                vlan_start <= other.vlan_end
                and vlan_end >= other.vlan_start
            ):

                stag_names = (
                    ", ".join(
                        [s.name for s in stags]
                    )
                    if stags
                    else "No STags"
                )

                raise serializers.ValidationError(
                    {
                        "vlan_range":
                        f"VLAN range overlaps "
                        f"with '{other.name}' "
                        f"in the same datacenter "
                        f"for the same company "
                        f"and STag(s): "
                        f"{stag_names}."
                    }
                )

        # -------------------------
        # Group permission validation
        # -------------------------
        if instance and user:
            has_permission = instance.groups.filter(
                id__in=user.groups.values_list(
                    "id",
                    flat=True
                )
            ).exists()

            if not has_permission:
                raise PermissionDenied(
                    "You do not have permission "
                    "to edit this TagRange."
                )

        return attrs


class STagSerializer(serializers.ModelSerializer):
    class Meta:
        model = STag
        fields = "__all__"