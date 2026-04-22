"""
Author: Sakhele George Mndaweni
Created: 2026-01-29
"""
from rest_framework import serializers
from .models import *
from rest_framework import serializers



class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"

    def validate(self, data):
        vlan = data.get("vlan")
        vlan_range = data.get("vlan_range")

        if vlan_range and not (vlan_range.vlan_start <= vlan <= vlan_range.vlan_end):
            raise serializers.ValidationError(
                {"vlan": "VLAN outside assigned range"}
            )
        return data

class VlanActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = VlanActivity
        fields = ['id', 'vlan_id', 'message', 'level', 'timestamp']




