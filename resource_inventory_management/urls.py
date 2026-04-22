from django.urls import path
from . import views

urlpatterns = [
    path("tmf-api/resourceInventoryManagement/v4/resource", views.list_resources, name="list_resources"),
    path("tmf-api/resourceInventoryManagement/v4/resource/<str:Service_id>", views.retrieve_resource, name="retrieve_resource"),
    path("tmf-api/resourceInventoryManagement/v4/resource/create/", views.create_resource, name="create_resource"),
    path("tmf-api/resourceInventoryManagement/v4/resource/<str:Service_id>/patch", views.patch_resource, name="patch_resource"),
    path("tmf-api/resourceInventoryManagement/v4/resource/<str:Service_id>/delete", views.delete_resource, name="delete_resource"),
    path("tmf-api/resourceInventoryManagement/v4/token", views.generate_token, name="generate_token"),
]