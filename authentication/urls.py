# accounts/urls.py
from django.urls import path
from .views import login_view, change_password_view

urlpatterns = [
    path("login/", login_view, name="login"),
    path("change-password/", change_password_view, name="change_password"),
]
