from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse


def send_verification_email(user, request):
    """
    Send email verification link to user.
    
    Args:
        user: CustomUser instance
        request: HTTP request object for building absolute URLs
    """
    # Generate verification token
    token = user.generate_verification_token()
    user.save(update_fields=['email_verification_token'])
    
    # Build verification URL
    verification_url = request.build_absolute_uri(
        reverse('users:verify_email', kwargs={'token': token})
    )
    
    # Email context
    context = {
        'user': user,
        'verification_url': verification_url,
        'site_name': 'Trading Dashboard',
    }
    
    # Render email
    html_message = render_to_string('emails/verify_email.html', context)
    plain_message = strip_tags(html_message)
    
    # Send email
    send_mail(
        subject='Verify your email address',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_password_reset_email(user, request):
    """
    Send password reset link to user.
    
    Args:
        user: CustomUser instance
        request: HTTP request object for building absolute URLs
    """
    # Generate reset token
    token = user.generate_verification_token()  # Reuse token generation
    user.save(update_fields=['email_verification_token'])
    
    # Build reset URL
    reset_url = request.build_absolute_uri(
        reverse('users:password_reset_confirm', kwargs={'token': token})
    )
    
    # Email context
    context = {
        'user': user,
        'reset_url': reset_url,
        'site_name': 'Trading Dashboard',
    }
    
    # Render email
    html_message = render_to_string('emails/password_reset.html', context)
    plain_message = strip_tags(html_message)
    
    # Send email
    send_mail(
        subject='Reset your password',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_machine_id_confirmation(user):
    """
    Send confirmation email when machine ID is registered.
    
    Args:
        user: CustomUser instance
    """
    context = {
        'user': user,
        'site_name': 'Trading Dashboard',
    }
    
    # Render email
    html_message = render_to_string('emails/machine_id_confirmed.html', context)
    plain_message = strip_tags(html_message)
    
    # Send email
    send_mail(
        subject='Machine ID Registered',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )
