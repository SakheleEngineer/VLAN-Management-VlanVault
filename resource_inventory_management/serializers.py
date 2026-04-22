from rest_framework import serializers
from .models import Tag
from .models import *

# Sub-resource serializers
class CharacteristicSerializer(serializers.Serializer):
    id = serializers.CharField(required=False)
    name = serializers.CharField()
    value = serializers.CharField()
    valueType = serializers.CharField(default="string")
    characteristicRelationship = serializers.ListField(child=serializers.DictField(), required=False)


class RelatedPartySerializer(serializers.Serializer):
    id = serializers.CharField(required=False)
    href = serializers.CharField(required=False)
    name = serializers.CharField()
    role = serializers.CharField()
    referredType = serializers.CharField(default="Individual")


class NoteSerializer(serializers.Serializer):
    id = serializers.CharField(required=False)
    text = serializers.CharField()
    author = serializers.CharField(required=False)
    date = serializers.DateTimeField(required=False)


class ResourceRelationshipSerializer(serializers.Serializer):
    relationshipType = serializers.CharField()
    resource = serializers.DictField()  # {'id':..., 'href':...}


class RelatedPlaceSerializer(serializers.Serializer):
    id = serializers.CharField()
    href = serializers.CharField()
    name = serializers.CharField()
    role = serializers.CharField(required=False)
    referredType = serializers.CharField(required=False)


class ResourceSpecificationRefSerializer(serializers.Serializer):
    id = serializers.CharField()
    href = serializers.CharField()
    name = serializers.CharField(required=False)
    version = serializers.CharField(required=False)
    referredType = serializers.CharField(required=False)


class AttachmentSerializer(serializers.Serializer):
    id = serializers.CharField()
    href = serializers.CharField()
    name = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    attachmentType = serializers.CharField(required=False)
    url = serializers.CharField(required=False)
    mimeType = serializers.CharField(required=False)
    content = serializers.CharField(required=False)
    size = serializers.DictField(required=False)
    validFor = serializers.DictField(required=False)

# Main Resource serializer
class TagResourceSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk')
    href = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    category = serializers.CharField(source='vlan_range.datacenter.region', read_only=True)

    resourceStatus = serializers.SerializerMethodField()
    usageState = serializers.SerializerMethodField()
    resourceCharacteristic = serializers.SerializerMethodField()
    relatedParty = serializers.SerializerMethodField()
    note = serializers.SerializerMethodField()
    resourceRelationship = serializers.SerializerMethodField()
    place = serializers.SerializerMethodField()
    resourceSpecification = serializers.SerializerMethodField()
    attachment = serializers.SerializerMethodField()
    activationFeature = serializers.SerializerMethodField()
    administrativeState = serializers.SerializerMethodField()
    operationalState = serializers.SerializerMethodField()
    startOperatingDate = serializers.DateTimeField(source='vlan_range.startOperatingDate', required=False)
    endOperatingDate = serializers.DateTimeField(source='vlan_range.endOperatingDate', required=False)
    resourceVersion = serializers.CharField(source='vlan_range.resourceVersion', required=False)

    class Meta:
        model = Tag
        fields = [
            "id",
            "href",
            "name",
            "category",
            "resourceStatus",
            "usageState",
            "resourceCharacteristic",
            "relatedParty",
            "note",
            "resourceRelationship",
            "place",
            "resourceSpecification",
            "attachment",
            "activationFeature",
            "administrativeState",
            "operationalState",
            "startOperatingDate",
            "endOperatingDate",
            "resourceVersion",
        ]

    def get_href(self, obj):
        return f"/tmf-api/resourceInventoryManagement/v4/resource/{obj.Service_id}"  # Use Service_id PK

    def get_name(self, obj):
        return str(obj.vlan)

    def get_resourceStatus(self, obj):
        return "reserved" if obj.usage else "available"

    def get_usageState(self, obj):
        return "busy" if obj.usage else "idle"

    def get_resourceCharacteristic(self, obj):
        characteristics = []
        if obj.division:
            characteristics.append({"name": "division", "value": obj.division})
        if obj.service:
            characteristics.append({"name": "service", "value": obj.service})
        if obj.speed:
            characteristics.append({"name": "speed", "value": obj.speed})
        return characteristics

    def get_relatedParty(self, obj):
        parties = []
        if obj.customer:
            parties.append({"id": obj.customer, "name": obj.customer, "role": "customer"})
        return parties

    def get_note(self, obj):
        # Return as dict list instead of Note instance
        if obj.comment:
            return [{"text": obj.comment}]
        return []

    def get_resourceRelationship(self, obj):
        if obj.vlan_range:
            return [{
                "relationshipType": "belongsToRange",
                "resource": {
                    "id": obj.vlan_range.id,
                    "name": str(obj.vlan_range),
                    "href": f"/tmf-api/resourceInventoryManagement/v4/resourceRange/{obj.vlan_range.id}"
                }
            }]
        return []

    def get_place(self, obj):
        p = getattr(obj.vlan_range, "place", None)
        if p:
            return {
                "id": p.id,
                "href": p.href,
                "name": p.name,
                "role": getattr(p, "role", ""),
                "referredType": "Place"
            }
        return None

    def get_resourceSpecification(self, obj):
        rs = getattr(obj.vlan_range, "resourceSpecification", None)
        if rs:
            return {
                "id": rs.id,
                "href": rs.href,
                "name": getattr(rs, "name", ""),
                "version": getattr(rs, "version", ""),
                "referredType": getattr(rs, "referredType", "")
            }
        return None

    def get_attachment(self, obj):
        return getattr(obj.vlan_range, "attachment", [])

    def get_activationFeature(self, obj):
        return getattr(obj.vlan_range, "activationFeature", [])

    def get_administrativeState(self, obj):
        return getattr(obj.vlan_range, "administrativeState", "unlocked")

    def get_operationalState(self, obj):
        return getattr(obj.vlan_range, "operationalState", "enable")