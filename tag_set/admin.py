from django.contrib import admin
from .models import TagRange


@admin.register(TagRange)
class TagRangeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "vlan_start",
        "vlan_end",
        "datacenter",
        "company",
        "uuid",
    )

    list_filter = (
        "datacenter",
        "company",
    )

    search_fields = (
        "name",
        "uuid",
    )

    ordering = (
        "vlan_start",
    )

    readonly_fields = (
        "uuid",
    )

    # Makes ManyToMany easier to manage
    filter_horizontal = (
        "groups",
        "stags",
    )

    fieldsets = (
        (
            "Tag Range Details",
            {
                "fields": (
                    "name",
                    "vlan_start",
                    "vlan_end",
                    "groups",   # ADD THIS
                    "stags",    # optional
                )
            },
        ),
        (
            "Ownership",
            {
                "fields": (
                    "datacenter",
                    "company",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "uuid",
                )
            },
        ),
    )