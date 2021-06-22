from .models import Product
from django import forms

class ProductModelForm(forms.ModelForm):
    
    class Meta:
        model = Product
        fields = [
            "name",
            "email",
            "phone",
            "comments",
            "time_slot",
        ]
