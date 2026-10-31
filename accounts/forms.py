from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

class CreatorSignupForm(UserCreationForm):
    display_name = forms.CharField(max_length=80, min_length=2, label="Your name")
    email = forms.EmailField(max_length=254, label="Email address")

    class Meta:
        model = User
        fields = ("email",)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["display_name"].strip()
        user.is_active = False
        if commit:
            user.save()
        return user

class CreatorLoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email address", widget=forms.EmailInput(attrs={"autocomplete": "email"}))
