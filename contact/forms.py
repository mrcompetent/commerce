# contact/forms.py
from django import forms
from .models import ContactMessage


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "input",
                "placeholder": "Your full name",
            }),
            "email": forms.EmailInput(attrs={
                "class": "input",
                "placeholder": "you@example.com",
            }),
            "subject": forms.TextInput(attrs={
                "class": "input",
                "placeholder": "Subject",
            }),
            "message": forms.Textarea(attrs={
                "class": "input",
                "placeholder": "Write your message here...",
                "rows": 5,
            }),
        }
