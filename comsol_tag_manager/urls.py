
from django.contrib import admin
from django.urls import path, include
from home import views
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('', include('tag_set.urls')),
    path('', include('data_center.urls')),
    path('', include('region.urls')),
    path('', include('company.urls')),
    path('', include('tag.urls')),
    path('', include('tag_history.urls')),
    path('', include('authentication.urls')),
    path('', include('resource_inventory_management.urls')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)