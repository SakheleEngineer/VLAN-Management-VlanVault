
"""
Author: Sakhele George Mndaweni
Created: 2026-01-29
"""
from django import forms
from django.core.exceptions import ValidationError
from .models import Tag

class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = [
            'vlan', 'division', 'customer', 'name', 'access_hs', 'sector',
            'usage', 'service', 'speed', 'circ_no', 'Service_id', 'comment', 'vlan_range'
        ]
        labels = {
            'vlan': 'VLAN ID',
            'division': 'Division',
            'customer': 'Customer Name',
            'name': 'Tag Name',
            'access_hs': 'Access HS',
            'sector': 'Sector',
            'usage': 'Usage Type',
            'service': 'Service Type',
            'speed': 'Speed',
            'circ_no': 'Circuit Number',
            'Service_id': 'Service ID',
            'comment': 'Comments',
            'vlan_range': 'VLAN Range',
        }
        help_texts = {
            'Service_id': 'Enter the ServiceNow Service ID to auto-fill service details.',
        }
        widgets = {
            'division': forms.TextInput(attrs={'class': 'form-control form-control-sm input-group input-group-sm mb-3'}),
            'customer': forms.TextInput(attrs={'class': 'form-control form-control-sm '}),
            'name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'access_hs': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'sector': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'usage': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'service': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'speed': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'circ_no': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'Service_id': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'comment': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'vlan': forms.NumberInput(attrs={'class': 'form-control form-control-sm','disabled': 'disabled'}),
            'vlan_range': forms.Select(attrs={'class': 'form-control form-control-sm ','disabled': 'disabled'}),
        }

    def clean_vlan(self):
        vlan = self.cleaned_data.get('vlan')
        vlan_range = self.cleaned_data.get('vlan_range')
        if vlan_range and not (vlan_range.vlan_start <= vlan <= vlan_range.vlan_end):
            raise ValidationError("VLAN outside assigned range")
        return vlan
