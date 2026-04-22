# serializers.py
from rest_framework import serializers
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

class STagSerializer(serializers.ModelSerializer):
    class Meta:
        model = STag
        fields = "__all__"