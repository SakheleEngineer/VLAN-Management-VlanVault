from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from .models import DataCenter
from .serializers import DataCenterSerializer
from rest_framework.decorators import action
from .forms import DataCenterForm
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


@method_decorator(login_required, name='dispatch')
class DataCenterViewSet(ModelViewSet):
    queryset = DataCenter.objects.all()
    serializer_class = DataCenterSerializer

    @action(detail=False, methods=['get'], url_path='list-view')
    def list_view(self, request):
        return render(
            request,
            "data_centers.html",
            {
                "datacenters": DataCenter.objects.all(),
                "form": DataCenterForm(),
            }
        )




