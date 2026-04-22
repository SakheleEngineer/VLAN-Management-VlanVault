from rest_framework.viewsets import ModelViewSet
from .models import *
from .serializers import *
from rest_framework.decorators import action
from django.shortcuts import render
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from .forms import *
from rest_framework import status
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from django.db.models import Case, When, Value, IntegerField
from django.db.models import Case, When, Value, IntegerField, F, Count, ExpressionWrapper
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


@method_decorator(login_required, name='dispatch')
class TagRangeViewSet(ModelViewSet):
    queryset = TagRange.objects.all()
    serializer_class = TagRangeSerializer
    parser_classes = [FormParser, MultiPartParser, JSONParser]

    @action(detail=False, methods=['get'], url_path='list-view')
    def list_view(self, request):
        queryset = self.get_queryset().select_related('datacenter').annotate(
            total_vlans=ExpressionWrapper(
                F('vlan_end') - F('vlan_start') + 1,
                output_field=IntegerField()
            ),
            used_vlans=Count('tag'),  
        ).annotate(
            free_vlans=ExpressionWrapper(
                F('total_vlans') - F('used_vlans'),
                output_field=IntegerField()
            ),
            datacenter_priority=Case(
                When(datacenter__region='JHB', then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        ).order_by('datacenter_priority', 'datacenter__region', 'vlan_start', 'vlan_end')

        form = TagRangeForm()
        return render(request, 'tag_sets.html', {
            'tagsets': queryset,
            'rangeForm': form
        })

    def perform_clean(self, instance, stags):
        # Temporarily store stags for validation in model.clean()
        instance._stags_temp = stags
        try:
            instance.full_clean()
        except ValidationError as e:
            raise ValidationError(e.message_dict or e.messages)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Extract stags separately because it's M2M
        stags = serializer.validated_data.pop('stags', [])

        # Create instance without stags
        instance = TagRange(**serializer.validated_data)

        # Validate with temp stags
        self.perform_clean(instance, stags)

        # Save instance first
        instance.save()

        # Set the many-to-many stags properly
        instance.stags.set(stags)

        # Re-serialize with saved instance and return response
        output_serializer = self.get_serializer(instance)
        headers = self.get_success_headers(output_serializer.data)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        stags = serializer.validated_data.pop('stags', [])

        # Update instance fields except stags
        for attr, value in serializer.validated_data.items():
            setattr(instance, attr, value)

        # Validate with temp stags
        self.perform_clean(instance, stags)

        instance.save()

        # Update many-to-many field
        instance.stags.set(stags)

        output_serializer = self.get_serializer(instance)
        return Response(output_serializer.data)
  
class STagViewSet(ModelViewSet):
    queryset = STag.objects.all()
    serializer_class = STagSerializer