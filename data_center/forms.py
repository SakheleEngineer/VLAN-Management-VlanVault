from django import forms
from .models import DataCenter


class DataCenterForm(forms.ModelForm):
    class Meta:
        model = DataCenter
        fields = ['name', 'location', 'region']
        labels = {
            'name': 'Data Center Name',
            'location': 'Location',
            'region': 'Region',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'e.g. JHB-DC01'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'e.g. Johannesburg'
            }),
            'region': forms.TextInput(attrs={
                'class': 'form-control form-control-sm'
            }),
        }
