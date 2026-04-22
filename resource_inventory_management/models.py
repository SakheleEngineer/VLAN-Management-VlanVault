from django.db import models
from tag.models import Tag
# -----------------------------
# COMMON SUB-OBJECTS
# -----------------------------
class TimePeriod(models.Model):
    startDateTime = models.DateTimeField(null=True, blank=True)
    endDateTime = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.startDateTime} - {self.endDateTime}"


class Quantity(models.Model):
    amount = models.FloatField()
    units = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.amount} {self.units}"


# -----------------------------
# RESOURCE SPECIFICATION REF
# -----------------------------
class ResourceSpecificationRef(models.Model):
    tmf_id = models.CharField(max_length=100)
    referredType = models.CharField(max_length=100, null=True, blank=True)
    href = models.URLField()
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name} ({self.tmf_id})"


# -----------------------------
# CONSTRAINT REF
# -----------------------------
class ConstraintRef(models.Model):
    tmf_id = models.CharField(max_length=100)
    referredType = models.CharField(max_length=100, null=True, blank=True)
    href = models.URLField()
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name} ({self.tmf_id})"


# -----------------------------
# ATTACHMENT
# -----------------------------
class AttachmentRefOrValue(models.Model):
    tmf_id = models.CharField(max_length=100)
    referredType = models.CharField(max_length=100, null=True, blank=True)
    href = models.URLField(null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    url = models.URLField(null=True, blank=True)
    attachmentType = models.CharField(max_length=100, null=True, blank=True)
    content = models.TextField(null=True, blank=True)  # base64 encoded
    mimeType = models.CharField(max_length=100, null=True, blank=True)
    size = models.ForeignKey(Quantity, null=True, blank=True, on_delete=models.SET_NULL, related_name="attachments")
    validFor = models.ForeignKey(TimePeriod, null=True, blank=True, on_delete=models.SET_NULL, related_name="attachments")

    def __str__(self):
        return f"{self.name} ({self.tmf_id})"


# -----------------------------
# RELATED PARTY
# -----------------------------
class RelatedParty(models.Model):
    tmf_id = models.CharField(max_length=100)
    referredType = models.CharField(max_length=100, null=True, blank=True)
    href = models.URLField(null=True, blank=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.role})"


# -----------------------------
# PLACE
# -----------------------------
class RelatedPlaceRefOrValue(models.Model):
    tmf_id = models.CharField(max_length=100)
    referredType = models.CharField(max_length=100, null=True, blank=True)
    href = models.URLField(null=True, blank=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name


# -----------------------------
# NOTE
# -----------------------------
class Note(models.Model):
    tmf_id = models.CharField(max_length=100)
    author = models.CharField(max_length=255)
    date = models.DateTimeField()
    text = models.TextField()

    def __str__(self):
        return f"{self.text[:50]}"


# -----------------------------
# CHARACTERISTIC RELATIONSHIP
# -----------------------------
class CharacteristicRelationship(models.Model):
    tmf_id = models.CharField(max_length=100)
    relationshipType = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.relationshipType} ({self.tmf_id})"


# -----------------------------
# CHARACTERISTIC
# -----------------------------
class Characteristic(models.Model):
    tmf_id = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    value = models.JSONField(null=True, blank=True)
    valueType = models.CharField(max_length=50)
    relationships = models.ManyToManyField(
        CharacteristicRelationship, blank=True, related_name="characteristics"
    )

    def __str__(self):
        return f"{self.name} ({self.tmf_id})"


# -----------------------------
# FEATURE RELATIONSHIP
# -----------------------------
class FeatureRelationship(models.Model):
    tmf_id = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    relationshipType = models.CharField(max_length=100)
    validFor = models.ForeignKey(TimePeriod, null=True, blank=True, on_delete=models.SET_NULL, related_name="feature_relationships")

    def __str__(self):
        return f"{self.name} ({self.relationshipType})"


# -----------------------------
# FEATURE
# -----------------------------
class Feature(models.Model):
    tmf_id = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    isBundle = models.BooleanField(default=False)
    isEnabled = models.BooleanField(default=True)
    constraint = models.ManyToManyField(ConstraintRef, blank=True, related_name="features")
    featureCharacteristic = models.ManyToManyField(Characteristic, related_name="features")
    featureRelationship = models.ManyToManyField(FeatureRelationship, blank=True, related_name="features")

    def __str__(self):
        return self.name


# -----------------------------
# RESOURCE REF OR VALUE
# -----------------------------
class ResourceRefOrValue(models.Model):
    tmf_id = models.CharField(max_length=100)
    referredType = models.CharField(max_length=100, null=True, blank=True)
    href = models.URLField(null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=255, null=True, blank=True)
    resourceVersion = models.CharField(max_length=50, null=True, blank=True)
    startOperatingDate = models.DateTimeField(null=True, blank=True)
    endOperatingDate = models.DateTimeField(null=True, blank=True)

    activationFeature = models.ManyToManyField(Feature, blank=True, related_name="resources_activation")
    attachment = models.ManyToManyField(AttachmentRefOrValue, blank=True, related_name="resources_attachment")
    note = models.ManyToManyField(Note, blank=True, related_name="resources_note")
    place = models.ForeignKey(RelatedPlaceRefOrValue, null=True, blank=True, on_delete=models.SET_NULL, related_name="resources")
    relatedParty = models.ManyToManyField(RelatedParty, blank=True, related_name="resources")
    resourceCharacteristic = models.ManyToManyField(Characteristic, blank=True, related_name="resources_characteristic")

    def __str__(self):
        return self.name


# -----------------------------
# RESOURCE RELATIONSHIP
# -----------------------------
class ResourceRelationship(models.Model):
    relationshipType = models.CharField(max_length=100)
    resource = models.ForeignKey(ResourceRefOrValue, on_delete=models.CASCADE, related_name="resource_relationships")

    def __str__(self):
        return f"{self.relationshipType} -> {self.resource}"


# -----------------------------
# MAIN RESOURCE
# -----------------------------
class Resource(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    href = models.URLField(null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=255, null=True, blank=True)
    resourceVersion = models.CharField(max_length=50, null=True, blank=True)
    startOperatingDate = models.DateTimeField(null=True, blank=True)
    endOperatingDate = models.DateTimeField(null=True, blank=True)

    administrativeState = models.CharField(max_length=50, default="unlocked", blank=True)
    operationalState = models.CharField(max_length=50, default="enable", blank=True)
    resourceStatus = models.CharField(max_length=50, default="available", blank=True)
    usageState = models.CharField(max_length=50, default="idle", blank=True)

    activationFeature = models.ManyToManyField(Feature, blank=True, related_name="resources")
    attachment = models.ManyToManyField(AttachmentRefOrValue, blank=True, related_name="resources_main")
    note = models.ManyToManyField(Note, blank=True, related_name="resources_main")
    place = models.ForeignKey(RelatedPlaceRefOrValue, null=True, blank=True, on_delete=models.SET_NULL, related_name="resources_main")
    relatedParty = models.ManyToManyField(RelatedParty, blank=True, related_name="resources_main")
    resourceCharacteristic = models.ManyToManyField(Characteristic, blank=True, related_name="resources_main")
    resourceRelationship = models.ManyToManyField(ResourceRelationship, blank=True, related_name="resources_main")
    resourceSpecification = models.ForeignKey(ResourceSpecificationRef, null=True, blank=True, on_delete=models.SET_NULL, related_name="resources_main")

    def __str__(self):
        return f"{self.name} ({self.id})"