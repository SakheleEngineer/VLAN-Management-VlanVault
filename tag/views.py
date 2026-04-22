"""
Author: Sakhele George Mndaweni
Created: 2026-01-29
"""
from rest_framework.viewsets import ModelViewSet
from .models import *
from .serializers import TagSerializer
from rest_framework.decorators import action
import uuid
from django.shortcuts import render, get_object_or_404
from tag_set.models import  TagRange
from .forms import TagForm
from rest_framework import filters
from .models import VlanActivity
from .serializers import VlanActivitySerializer
from tag_set.forms import TagRangeForm
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.utils import timezone
from django.db import transaction
from taglib.tag_utility_library  import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from django.core.cache import cache

def get_posts():
    print("fetched", cache.get("external_posts"))

@method_decorator(login_required, name='dispatch')
class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    parser_classes = [FormParser, MultiPartParser, JSONParser]

    
    @action(
        detail=False,
        methods=['get'],
        url_path='list-view(?:/(?P<uuid_str>[^/.]+))?',
        url_name='list-view'
    )
    def list_by_range(self, request, uuid_str=None):
        
        rows = []
        uuid_obj = uuid.UUID(uuid_str)
        if uuid:
            tag_range = get_object_or_404(TagRange, uuid=uuid_obj)
            tags = Tag.objects.filter(vlan_range=tag_range).order_by('vlan')
            rangeForm = TagRangeForm(instance= tag_range)
            # Initialize the form with the default vlan_range
            form = TagForm(initial={'vlan_range': tag_range})

            prev = tag_range.vlan_start - 1

            for tag in tags:
                vlan = tag.vlan

                # Ignore duplicates or bad data
                if vlan <= prev:
                    continue

                # GAP of ONE OR MORE VLANs
                if vlan > prev + 1:
                    gap_start = prev + 1
                    gap_end = vlan - 1

                    rows.append({
                        "type": "free",
                        "start": gap_start,
                        "end": gap_end,
                        "count": gap_end - gap_start + 1,
                    })

                # CURRENT VLAN IS IN USE
                rows.append({
                    "type": "tag",
                    "obj": tag,
                })

                prev = vlan

            # GAP AFTER LAST TAG
            if prev < tag_range.vlan_end:
                gap_start = prev + 1
                gap_end = tag_range.vlan_end

                rows.append({
                    "type": "free",
                    "start": gap_start,
                    "end": gap_end,
                    "count": gap_end - gap_start + 1,
                })

        else:
            tag_range = None
            tags = Tag.objects.all().order_by('vlan') 

        return render(
            request,
            'tags.html',
            {
                'tag_range': tag_range,
                'tags':      tags,
                'rangeForm': rangeForm,
                'form':      form,
                'rows':      rows
            }
        )

    @action(detail=False, methods=["post"], url_path="auto-reserve")
    def auto_reserve(self, request):
        range_uuid = request.POST.get("range_uuid")
        csv_file = request.FILES.get("csv_file")

        if not csv_file:
            return Response({"success": False, "error": "No CSV uploaded"})

        tag_range = get_object_or_404(TagRange, uuid=range_uuid)

        # Process CSV here...

        return Response({"success": True})

    # @action(
    #     detail=False,
    #     methods=['get'],
    #     url_path='get-tagdata',
    #     url_name='get-tagdata'
    # )
    # def get_tag_data(self, request):
    #     service_id = request.GET.get("service_id")

    #     if not service_id:
    #         return Response({"error": "service_id is required"}, status=400)

    #     token = get_snow_session_token()
    #     data = get_snow_service_data(token, service_id)

    #     print("Data from SNOW:", data)

    #     if not data:
    #         return Response({"error": "No data found from SNOW"}, status=404)

    #     # ✅ Return Tag-like JSON (no DB write)
    #     tag_like_json = {
    #         "vlan": 0,
    #         "division": data.get("province", ""),
    #         "customer": data.get("end_company_name", ""),
    #         "name": data.get("end_company_name", ""),
    #         "access_hs": data.get("access_hs", ""),
    #         "sector": data.get("sector", ""),
    #         "usage": data.get("delevary_type", ""),
    #         "service": data.get("service", ""),
    #         "speed": data.get("speed", ""),
    #         "circ_no": data.get("circuit_id", ""),
    #         "Service_id": data.get("service_id", ""),
    #         "comment": "Auto-generated from SNOW"
    #     }

    #     return Response(tag_like_json)


class GetTagDataAPIView(APIView):

    def get(self, request):
        service_id = request.GET.get("service_id")

        if not service_id:
            return Response(
                {"error": "service_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        print("Received service_id:", service_id)

        token = get_snow_session_token()
        data = get_snow_service_data(token, service_id)

        print("Data from SNOW:", data)

        if not data:
            return Response(
                {"error": "No data found from SNOW"},
                status=status.HTTP_404_NOT_FOUND
            )

        temp = data.get("sector", "")

        sector = f"Sector-{temp.split('-')[-1]}"  # "3"

        tag_like_json = {
            "vlan": 0,
            "division": 'CN',
            "customer":data.get("name", ""),
            "name": data.get("end_company_name", ""),
            "access_hs": data.get("access_hs", ""),
            "sector": sector,
            "usage": data.get("delevary_type", ""),
            "service": data.get("service", ""),
            "speed": data.get("speed", ""),
            "circ_no": data.get("circuit_id", ""),
            "service_id": data.get("service_id", ""),
            "comment": "Auto-generated from SNOW"

        }

        return Response(tag_like_json, status=status.HTTP_200_OK)




class VlanActivityViewSet(ModelViewSet):
    """
    Full CRUD for VLAN activities
    """
    queryset = VlanActivity.objects.all().order_by('-timestamp')
    serializer_class = VlanActivitySerializer
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['timestamp', 'vlan_id', 'level']
    ordering = ['-timestamp']
    search_fields = ['message', 'level', 'vlan_id']


class VlanLogViewSet(viewsets.ModelViewSet):
    queryset = VlanActivity.objects.all().order_by('-id')
    serializer_class = VlanActivitySerializer
    permission_classes = []  # or IsAuthenticated

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        log = response.data

        # Broadcast to websocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "vlan_logs",
            {
                "type": "send_log",
                "log": log
            }
        )
        return response


