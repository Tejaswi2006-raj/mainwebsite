from django import forms
from .models import Events

class EventImageForm(forms.ModelForm):
    class Meta:
        model = Events
        fields = ['image']
        widgets = {
            'image': forms.ClearableFileInput(attrs={'class': 'form-control', 'required': 'true'})
        }