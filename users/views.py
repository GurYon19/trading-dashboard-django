from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse

from payments.models import Trial, Subscription
from .models import CustomUser
from .forms import RegistrationForm, MachineIDForm, PasswordResetRequestForm, PasswordResetConfirmForm
from .emails import send_verification_email, send_password_reset_email, send_machine_id_confirmation


def register_view(request):
    """User registration with email verification."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email_verified = False  # Require email verification
            user.save()
            
            # Send verification email
            try:
                send_verification_email(user, request)
                messages.success(
                    request,
                    'Registration successful! Please check your email to verify your account.'
                )
                return redirect('users:login')
            except Exception as e:
                messages.error(
                    request,
                    f'Account created but failed to send verification email: {str(e)}'
                )
                return redirect('users:login')
    else:
        form = RegistrationForm()
    
    return render(request, 'users/register.html', {'form': form})


def verify_email_view(request, token):
    """Verify user email with token."""
    user = get_object_or_404(CustomUser, email_verification_token=token)
    
    if user.email_verified:
        messages.info(request, 'Your email is already verified.')
    else:
        user.email_verified = True
        user.email_verification_token = ''  # Clear token
        user.save(update_fields=['email_verified', 'email_verification_token'])
        messages.success(request, 'Email verified successfully! You can now log in.')
    
    return redirect('users:login')


@login_required
def set_machine_id_view(request):
    """Set machine ID (one-time only)."""
    user = request.user
    
    # Check if machine ID already set
    if user.has_machine_id:
        messages.warning(request, 'Machine ID is already set and cannot be changed.')
        return redirect('users:profile')
    
    if request.method == 'POST':
        form = MachineIDForm(request.POST)
        if form.is_valid():
            machine_id = form.cleaned_data['machine_id']
            
            # Set machine ID (hashed internally)
            if user.set_machine_id(machine_id):
                # Send confirmation email
                try:
                    send_machine_id_confirmation(user)
                except:
                    pass  # Don't fail if email fails
                
                messages.success(
                    request,
                    'Machine ID registered successfully! You can now download strategies and start trials.'
                )
                return redirect('users:profile')
            else:
                messages.error(request, 'Failed to set machine ID. Please try again.')
    else:
        form = MachineIDForm()
    
    return render(request, 'users/set_machine_id.html', {'form': form})


def password_reset_request_view(request):
    """Request password reset."""
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = CustomUser.objects.get(email=email)
            
            try:
                send_password_reset_email(user, request)
                messages.success(
                    request,
                    'Password reset link sent to your email.'
                )
            except Exception as e:
                messages.error(
                    request,
                    f'Failed to send reset email: {str(e)}'
                )
            
            return redirect('users:login')
    else:
        form = PasswordResetRequestForm()
    
    return render(request, 'users/password_reset_request.html', {'form': form})


def password_reset_confirm_view(request, token):
    """Confirm password reset with new password."""
    user = get_object_or_404(CustomUser, email_verification_token=token)
    
    if request.method == 'POST':
        form = PasswordResetConfirmForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['password1']
            user.set_password(new_password)
            user.email_verification_token = ''  # Clear token
            user.save()
            
            messages.success(request, 'Password reset successful! You can now log in.')
            return redirect('users:login')
    else:
        form = PasswordResetConfirmForm()
    
    return render(request, 'users/password_reset_confirm.html', {'form': form, 'token': token})


@login_required
def profile(request):
    """
    User profile / My Account page.

    Shows:
    - basic user info
    - machine ID status
    - free trials (active + ended)
    - paid access (rentals + lifetime)
    """
    user = request.user

    trials = (
        Trial.objects.filter(user=user)
        .order_by("-started_at")
    )
    subscriptions = (
        Subscription.objects.filter(user=user)
        .order_by("-started_at")
    )

    return render(
        request,
        "users/profile.html",
        {
            "user": user,
            "trials": trials,
            "subscriptions": subscriptions,
        },
    )


@login_required
def settings(request):
    """Account settings page."""
    if request.method == "POST":
        user = request.user
        user.first_name = request.POST.get("first_name", "")
        user.last_name = request.POST.get("last_name", "")
        # Machine ID cannot be changed once set
        user.save()
        messages.success(request, "Settings updated successfully!")
        return redirect("users:settings")

    return render(
        request,
        "users/settings.html",
        {
            "user": request.user,
        },
    )
