
# Register your models here.
from django.contrib import admin
from .models import Company, ENNI


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "code",
        "companytype",
        "city",
        "state_province",
        "country",
    )

    list_filter = (
        "companytype",
        "country",
        "city",
        "state_province",
    )

    search_fields = (
        "name",
        "code",
        "companytype",
        "street",
        "city",
        "state_province",
        "postal_code",
        "country",
    )

    ordering = (
        "name",
    )

    fieldsets = (
        (
            "Company Details",
            {
                "fields": (
                    "name",
                    "code",
                    "companytype",
                )
            },
        ),

        (
            "Address Details",
            {
                "fields": (
                    "street",
                    "city",
                    "state_province",
                    "postal_code",
                    "country",
                )
            },
        ),

        (
            "Additional Information",
            {
                "fields": (
                    "notes",
                )
            },
        ),
    )


@admin.register(ENNI)
class ENNIAdmin(admin.ModelAdmin):

    list_display = (
        "so_number",
        "company",
        "description",
    )

    list_filter = (
        "company",
    )

    search_fields = (
        "so_number",
        "description",
        "company__name",
        "company__code",
    )

    ordering = (
        "so_number",
    )

    fieldsets = (
        (
            "ENNI Details",
            {
                "fields": (
                    "so_number",
                    "description",
                )
            },
        ),

        (
            "Company Assignment",
            {
                "fields": (
                    "company",
                )
            },
        ),
    )