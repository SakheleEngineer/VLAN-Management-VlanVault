from rest_framework import serializers
from .models import DataCenter
from tag_set.serializers import TagRangeSerializer

class DataCenterSerializer(serializers.ModelSerializer):
    tag_ranges = TagRangeSerializer(many=True, read_only=True)

    class Meta:
        model = DataCenter
        fields = "__all__"
