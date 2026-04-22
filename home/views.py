from django.shortcuts import render
from tag_set.models import TagRange
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


@login_required
def home(request):
    # You can pass dynamic data as a dictionary (context)
    tagranges = TagRange.objects.all()
    context = {'message': 'This is dynamic content','tagranges':tagranges} 
    return render(request, 'home.html', context)
