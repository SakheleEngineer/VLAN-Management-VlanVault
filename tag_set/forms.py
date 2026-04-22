"""
Author: Sakhele George Mndaweni
Created: 2026-01-29
Updated: 2026-02-24
"""
from django import forms
from .models import TagRange, STag


class TagRangeForm(forms.ModelForm):
    # Add STags multiple selection
    stags = forms.ModelMultipleChoiceField(
        queryset=STag.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',
            'size': 8,  # height of select box
        }),
        label="STags",
        help_text="Select existing STags or create new ones in the modal."
    )

    class Meta:
        model = TagRange
        fields = [
            'name',
            'vlan_start',
            'vlan_end',
            'datacenter',
            'company',
            'stags',
        ]
        labels = {
            'name': 'Range Name',
            'vlan_start': 'VLAN Start',
            'vlan_end': 'VLAN End',
            'datacenter': 'Data Center',
            'company': 'Company',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Core VLAN Range'
            }),
            'vlan_start': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 4094,
            }),
            'vlan_end': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 4094,
            }),
            'datacenter': forms.Select(attrs={
                'class': 'form-control'
            }),
            'company': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

    def clean(self):
        """
        Extra safety: enforce VLAN range logic at form level
        """
        cleaned_data = super().clean()
        vlan_start = cleaned_data.get('vlan_start')
        vlan_end = cleaned_data.get('vlan_end')

        if vlan_start is not None and vlan_end is not None:
            if vlan_start >= vlan_end:
                raise forms.ValidationError(
                    "VLAN start must be less than VLAN end."
                )

        # Optional: check for overlapping ranges for same company & same stag
        # Uncomment if you want this enforced at form level
   
        company = cleaned_data.get('company')
        stags = cleaned_data.get('stags')  # Could be empty queryset
        if company and vlan_start is not None and vlan_end is not None:
            # If no STags selected, we still want to check for TagRanges with no STags
            if not stags or len(stags) == 0:
                overlaps = TagRange.objects.filter(
                    company=company,
                    stags__isnull=True
                ).exclude(pk=self.instance.pk if self.instance else None).filter(
                    vlan_start__lt=vlan_end,
                    vlan_end__gt=vlan_start
                )
                if overlaps.exists():
                    raise forms.ValidationError(
                        "VLAN range overlaps with existing range for this company with no STag."
                    )
            else:
                for stag in stags:
                    overlaps = TagRange.objects.filter(
                        company=company,
                        stags=stag
                    ).exclude(pk=self.instance.pk if self.instance else None).filter(
                        vlan_start__lt=vlan_end,
                        vlan_end__gt=vlan_start
                    )
                    if overlaps.exists():
                        raise forms.ValidationError(
                            f"VLAN range overlaps with existing range for STag '{stag.name}' in this company."
                        )


        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance._stags_temp = self.cleaned_data.get('stags', [])
        if commit:
            instance.save()
            self.save_m2m()
        return instance