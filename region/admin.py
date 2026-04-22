from django.contrib import admin

from django.contrib import admin
from .models import Region


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "datacenter",
    )

    list_filter = (
        "datacenter",
    )

    search_fields = (
        "name",
        "code",
        "datacenter__name",
    )

    ordering = (
        "name",
    )

    fieldsets = (
        (
            "Region Details",
            {
                "fields": (
                    "name",
                    "code",
                )
            },
        ),
        (
            "Data Center Assignment",
            {
                "fields": (
                    "datacenter",
                )
            },
        ),
    )
    