from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from .models import Company
from .serializers import CompanySerializer
from rest_framework.decorators import action
from .forms import CompanyForm

class CompanyViewSet(ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

    @action(detail=False, methods=['get'], url_path='list-view')
    def list_view(self, request):
        form = CompanyForm()
        return render(request, 'companies.html', {'companies': self.get_queryset(), 'form': form})


