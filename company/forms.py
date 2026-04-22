from django import forms
from .models import Company


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            "name",
            "street",
            "city",
            "state_province",
            "postal_code",
            "country",
            "notes",
        ]

        labels = {
            "name": "Company Name",
            "street": "Street",
            "city": "City",
            "state_province": "State / Province",
            "postal_code": "Zip / Postal Code",
            "country": "Country",
            "notes": "Notes",
        }

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control form-control-sm"}),

            "street": forms.Textarea(attrs={
                "class": "form-control form-control-sm",
                "rows": 1 # smaller textarea
            }),
            "city": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "state_province": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "postal_code": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "country": forms.TextInput(attrs={"class": "form-control form-control-sm"}),

            "notes": forms.Textarea(attrs={
                "class": "form-control form-control-sm",
                "rows": 1  # smaller textarea
            }),
        }
