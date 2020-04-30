from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.forms import EmailField
from .validators import RegisteredEmailValidator

class UserRegistrationForm(UserCreationForm):

    class Meta:
        model = get_user_model()
        fields = ('email', 'name')

class LoginForm(AuthenticationForm):
    username = EmailField(widget=forms.EmailInput(attrs={'autofocus': True}))


class VerificationEmailForm(forms.Form):
    email = EmailField(widget=forms.EmailInput(attrs={'autofocus': True}), validators=(EmailField.default_validators + [RegisteredEmailValidator()]))