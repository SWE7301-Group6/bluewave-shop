from django import forms
from django.contrib.auth.models import User

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    class Meta:
        model = User
        fields = ["username", "email", "password"]

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class TOTPVerifyForm(forms.Form):
    code = forms.CharField(label="Authenticator code", max_length=6)

class TOTPSetupForm(forms.Form):
    confirm = forms.BooleanField(label="I have scanned the QR code in my authenticator app")

class APITokenRequestForm(forms.Form):
    email = forms.EmailField(required=False, help_text="Defaults to your account email.")
    password = forms.CharField(widget=forms.PasswordInput, help_text="Your BlueWave API password.")
