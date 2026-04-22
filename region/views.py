# views.py
from rest_framework.viewsets import ModelViewSet
from .models import Region
from .serializers import RegionSerializer
from rest_framework.decorators import action

class RegionViewSet(ModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer

    @action(detail=False, methods=['get'], url_path='list-view')
    def list_view(self, request):
        return render(request, 'regions.html', {'regions': self.get_queryset()})
