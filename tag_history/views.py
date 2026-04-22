from django.shortcuts import render

from rest_framework.viewsets import ModelViewSet
from .models import History
from .serializers import HistorySerializer
from rest_framework.decorators import action
from tag.models import Tag
from itertools import groupby
from operator import attrgetter
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


@method_decorator(login_required, name='dispatch')
class HistoryViewSet(ModelViewSet):
    queryset = History.objects.all().order_by("-created_at")
    serializer_class = HistorySerializer

    @action(detail=False, methods=['get'], url_path='list-view')
    def list_view(self, request):
        # Get all history ordered by VLAN, service_id, and latest history_date first
        # Get all history ordered by VLAN, VLAN Range, and latest history_date first
        # Get all historical records ordered by VLAN, VLAN range, latest first
        all_histories = Tag.history.all().order_by('vlan', 'vlan_range_id', '-history_date')

        # Keep only **one record per VLAN + VLAN range**
        unique_tags = []

        for (vlan, vlan_range_id), records in groupby(all_histories, key=attrgetter('vlan', 'vlan_range_id')):
            unique_tags.append(list(records)[0])  # pick the latest record per VLAN + range

        return render(request, 'history.html', {'tags': unique_tags})

@login_required
def tag_history_view(request, tag_id):
    history = Tag.history.filter(vlan=tag_id).order_by('history_date')

    changes_list = []
    previous = None

    for h in history:
        change_data = {}

        if previous:
            for field in Tag._meta.fields:
                field_name = field.name

                old = getattr(previous, field_name)
                new = getattr(h, field_name)

                if old != new:
                    change_data[field_name] = {
                        "old": old,
                        "new": new
                    }

        else:
            # First record (creation)
            change_data = {field.name: getattr(h, field.name) for field in Tag._meta.fields}

        changes_list.append({
            "history": h,
            "changes": change_data
        })

        previous = h

    return render(request, 'tag_history.html', {
        "changes_list": reversed(changes_list),  # latest first
        "tag_id": tag_id
    })