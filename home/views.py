from django.shortcuts import render,redirect
from tag_set.models import TagRange
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


# @login_required
def home(request):
     return redirect('/tagranges/list-view/')