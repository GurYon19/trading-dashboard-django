"""
Email functions for trial-related notifications.
"""
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_trial_started_email(user, trial):
    """
    Send email when trial starts.
    
    Args:
        user: CustomUser instance
        trial: Trial instance
    """
    context = {
        'user': user,
        'trial': trial,
        'site_name': 'Trading Dashboard',
    }
    
    html_message = render_to_string('emails/trial_started.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=f'Trial Started: {trial.strategy_name}',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_trial_expiring_email(user, trial):
    """
    Send email when trial is expiring soon (3 days before).
    
    Args:
        user: CustomUser instance
        trial: Trial instance
    """
    context = {
        'user': user,
        'trial': trial,
        'days_remaining': trial.days_remaining,
        'site_name': 'Trading Dashboard',
    }
    
    html_message = render_to_string('emails/trial_expiring.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=f'Trial Expiring Soon: {trial.strategy_name}',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_trial_expired_email(user, trial):
    """
    Send email when trial has expired.
    
    Args:
        user: CustomUser instance
        trial: Trial instance
    """
    context = {
        'user': user,
        'trial': trial,
        'site_name': 'Trading Dashboard',
    }
    
    html_message = render_to_string('emails/trial_expired.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=f'Trial Ended: {trial.strategy_name}',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_payment_success_email(user, subscription):
    """
    Send email when payment is successful.
    
    Args:
        user: CustomUser instance
        subscription: Subscription instance
    """
    context = {
        'user': user,
        'subscription': subscription,
        'site_name': 'Trading Dashboard',
    }
    
    html_message = render_to_string('emails/payment_success.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject='Payment Successful - Subscription Activated',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_payment_failed_email(user, subscription):
    """
    Send email when payment fails.
    
    Args:
        user: CustomUser instance
        subscription: Subscription instance
    """
    context = {
        'user': user,
        'subscription': subscription,
        'site_name': 'Trading Dashboard',
    }
    
    html_message = render_to_string('emails/payment_failed.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject='Payment Failed - Action Required',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_subscription_cancelled_email(user, subscription):
    """
    Send email when subscription is cancelled.
    
    Args:
        user: CustomUser instance
        subscription: Subscription instance
    """
    context = {
        'user': user,
        'subscription': subscription,
        'site_name': 'Trading Dashboard',
    }
    
    html_message = render_to_string('emails/subscription_cancelled.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject='Subscription Cancelled',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )
