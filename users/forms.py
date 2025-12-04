from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import CustomUser
import re


class RegistrationForm(UserCreationForm):
    """User registration form with email and password."""
    
    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email',
            'autocomplete': 'email'
        })
    )
    
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password',
            'autocomplete': 'new-password'
        })
    )
    
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password',
            'autocomplete': 'new-password'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ('email', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError('An account with this email already exists.')
        return email


class MachineIDForm(forms.Form):
    """Form for setting machine ID (one-time only)."""
    
    machine_id = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your Machine ID',
            'autocomplete': 'off'
        }),
        help_text='Your machine ID can only be set once and cannot be changed.'
    )
    
    def clean_machine_id(self):
        machine_id = self.cleaned_data.get('machine_id')
        
        # Validate format (alphanumeric, hyphens, underscores allowed)
        if not re.match(r'^[A-Za-z0-9_-]+$', machine_id):
            raise ValidationError(
                'Machine ID can only contain letters, numbers, hyphens, and underscores.'
            )
        
        # Minimum length check
        if len(machine_id) < 8:
            raise ValidationError('Machine ID must be at least 8 characters long.')
        
        return machine_id


class PasswordResetRequestForm(forms.Form):
    """Form for requesting password reset."""
    
    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email',
            'autocomplete': 'email'
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not CustomUser.objects.filter(email=email).exists():
            raise ValidationError('No account found with this email address.')
        return email


class PasswordResetConfirmForm(forms.Form):
    """Form for confirming password reset with new password."""
    
    password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password',
            'autocomplete': 'new-password'
        })
    )
    
    password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password',
            'autocomplete': 'new-password'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError('Passwords do not match.')
        
        return cleaned_data
