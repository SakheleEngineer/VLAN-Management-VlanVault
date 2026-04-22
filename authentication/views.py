
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .models import UserProfile

def login_view(request):
    if request.user.is_authenticated:
        profile = UserProfile.objects.get(user=request.user)
        if profile.first_login:
            return redirect("change_password")
        return redirect("/")  # home page

    form = AuthenticationForm(data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        profile = UserProfile.objects.get(user=user)
        if profile.first_login:
            return redirect("change_password")
        return redirect("/")
    return render(request, "account/login.html", {"form": form})


@login_required
def change_password_view(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)  # keep user logged in
        profile = UserProfile.objects.get(user=user)
        profile.first_login = False
        profile.save()
        messages.success(request, "Password changed successfully!")
        return redirect("/")
    return render(request, "account/change_password.html", {"form": form})
