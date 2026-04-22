from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from tag.models import Tag
from .serializers import TagResourceSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from taglib.tag_utility_library import get_snow_session_token, get_snow_service_data, search_and_reserve_vlan, allocate_first_free_tag_from_ranges
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def generate_token(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response(
            {"error": "Username and password are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(username=username, password=password)

    if user is None:
        return Response(
            {"error": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Get or create token
    token, created = Token.objects.get_or_create(user=user)

    return Response({
        "token": token.key
    })

    

# LIST RESOURCES
@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def list_resources(request):
    queryset = Tag.objects.all()
    category = request.GET.get("category")
    usage_state = request.GET.get("usageState")

    if category:
        queryset = queryset.filter(vlan_range__datacenter__region=category)
    if usage_state == "idle":
        queryset = queryset.filter(usage__isnull=True)
    elif usage_state == "busy":
        queryset = queryset.exclude(usage__isnull=True)

    serializer = TagResourceSerializer(queryset, many=True)
    data = serializer.data

    fields = request.GET.get("fields")
    if fields:
        fields = fields.split(",")
        data = [{k: v for k, v in item.items() if k in fields} for item in data]

    return Response(data)


# RETRIEVE RESOURCE
@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def retrieve_resource(request, Service_id):
    print(f"Retrieving resource with Service_id: {Service_id}")
    tag = get_object_or_404(Tag, Service_id=Service_id)

    serializer = TagResourceSerializer(tag)
    data = serializer.data

    fields = request.GET.get("fields")
    if fields:
        fields = fields.split(",")
        data = {k: v for k, v in data.items() if k in fields}

    return Response(data)


# CREATE RESOURCE
@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_resource(request):
    data = request.data
    service_id = data.get("name")
    if not service_id:
        return Response({"error": "VLAN value required"}, status=400)

    token = get_snow_session_token()
    snow_data = get_snow_service_data(token, service_id)
    allocated_tag = search_and_reserve_vlan(snow_data)
    if not allocated_tag:
        return Response({"error": "No available VLANs found"}, status=400)
    serializer = TagResourceSerializer(allocated_tag)
    return Response(serializer.data, status=201)


# PATCH RESOURCE
@api_view(["PATCH"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def patch_resource(request, service_id):
    tag = get_object_or_404(Tag, service_id=service_id)
    data = request.data

    patchable_fields = [
        "name", "division", "service", "speed", "sector",
        "customer", "comment", "usageState", "resourceStatus", "vlan_range"
    ]

    for field in patchable_fields:
        if field in data:
            if field == "resourceStatus":
                tag.usage = "reserved" if data["resourceStatus"] == "reserved" else ""
            elif field == "usageState":
                tag.usage = "reserved" if data["usageState"] == "busy" else ""
            elif field == "vlan_range":
                tag.vlan_range_id = data["vlan_range"]
            else:
                setattr(tag, field, data[field])

    tag.save()
    serializer = TagResourceSerializer(tag)
    return Response(serializer.data)


# DELETE RESOURCE
@api_view(["DELETE"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_resource(request, Service_id):
    tag = get_object_or_404(Tag, Service_id=Service_id)
    tag.delete()
    return Response(status=204)