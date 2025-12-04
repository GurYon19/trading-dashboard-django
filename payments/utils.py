"""
Trial management utilities for creating, checking, and expiring trials.
"""
from django.utils import timezone
from datetime import timedelta
from payments.models import Trial, TrialAbuseLog, TRIAL_DURATION_DAYS
from django.db import transaction


def can_start_trial(user, strategy_name: str) -> tuple[bool, str]:
    """
    Check if user can start a trial for the given strategy.
    
    Args:
        user: CustomUser instance
        strategy_name: Name of the strategy
        
    Returns:
        (can_start: bool, reason: str)
    """
    # Use the model's class method
    can_start, reason = Trial.can_user_start_trial(user, strategy_name)
    
    if not can_start:
        return False, reason
    
    # Additional abuse detection
    if detect_trial_abuse(user, strategy_name):
        return False, "Suspicious trial activity detected. Please contact support."
    
    return True, "OK"


@transaction.atomic
def start_trial(user, strategy_name: str) -> tuple[Trial, bool]:
    """
    Create a trial record for the user and strategy.
    
    Args:
        user: CustomUser instance
        strategy_name: Name of the strategy
        
    Returns:
        (trial: Trial instance, created: bool)
    """
    # Check if trial can be started
    can_start, reason = can_start_trial(user, strategy_name)
    if not can_start:
        raise ValueError(reason)
    
    # Calculate trial end date
    start_time = timezone.now()
    end_time = start_time + timedelta(days=TRIAL_DURATION_DAYS)
    
    # Create trial
    trial = Trial.objects.create(
        user=user,
        strategy_name=strategy_name,
        machine_id_snapshot=user.machine_id_hash,
        started_at=start_time,
        ends_at=end_time,
        status='active'
    )
    
    # Log trial attempt
    TrialAbuseLog.objects.create(
        email=user.email,
        machine_id_hash=user.machine_id_hash,
        strategy_name=strategy_name,
        user=user,
        blocked=False
    )
    
    return trial, True


def check_trial_access(user, strategy_name: str) -> bool:
    """
    Check if user has active trial access to a strategy.
    
    Args:
        user: CustomUser instance
        strategy_name: Name of the strategy
        
    Returns:
        bool: True if user has active trial access
    """
    try:
        trial = Trial.objects.get(
            user=user,
            strategy_name=strategy_name
        )
        return trial.is_active
    except Trial.DoesNotExist:
        return False


def expire_trials() -> int:
    """
    Expire all trials that have passed their end date.
    This should be run as a periodic task (cron job).
    
    Returns:
        int: Number of trials expired
    """
    expired_count = 0
    
    # Get all active trials that have ended
    active_trials = Trial.objects.filter(
        status='active',
        ends_at__lte=timezone.now()
    )
    
    for trial in active_trials:
        if trial.check_and_expire():
            expired_count += 1
    
    return expired_count


def detect_trial_abuse(user, strategy_name: str) -> bool:
    """
    Detect suspicious trial patterns.
    
    Args:
        user: CustomUser instance
        strategy_name: Name of the strategy
        
    Returns:
        bool: True if abuse detected
    """
    # Check if this machine ID has been used with different emails
    machine_id_hash = user.machine_id_hash
    
    # Count how many different emails have used this machine ID for trials
    different_emails = TrialAbuseLog.objects.filter(
        machine_id_hash=machine_id_hash
    ).values('email').distinct().count()
    
    # If more than 2 different emails used same machine ID, flag as suspicious
    if different_emails > 2:
        # Log as blocked
        TrialAbuseLog.objects.create(
            email=user.email,
            machine_id_hash=machine_id_hash,
            strategy_name=strategy_name,
            user=user,
            blocked=True
        )
        return True
    
    # Check if this email has tried multiple machine IDs
    different_machines = TrialAbuseLog.objects.filter(
        email=user.email
    ).values('machine_id_hash').distinct().count()
    
    # If more than 1 machine ID per email, flag as suspicious
    if different_machines > 1:
        TrialAbuseLog.objects.create(
            email=user.email,
            machine_id_hash=machine_id_hash,
            strategy_name=strategy_name,
            user=user,
            blocked=True
        )
        return True
    
    return False


def get_trials_expiring_soon(days_before: int = 3) -> list[Trial]:
    """
    Get trials that will expire within the specified number of days.
    Used for sending reminder emails.
    
    Args:
        days_before: Number of days before expiration
        
    Returns:
        list[Trial]: Trials expiring soon
    """
    cutoff_time = timezone.now() + timedelta(days=days_before)
    
    return Trial.objects.filter(
        status='active',
        ends_at__lte=cutoff_time,
        ends_at__gt=timezone.now()
    ).select_related('user')
