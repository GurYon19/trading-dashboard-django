from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


# Trial duration constant
TRIAL_DURATION_DAYS = 7


class Trial(models.Model):
    """
    Free trial for a strategy, tied to a specific user and (snapshotted) machine_id.
    Shown in the 'My Account' / profile section even after it ends.
    """

    STATUS_CHOICES = [
        ("active", "Active"),
        ("expired", "Expired"),
        ("converted", "Converted to Paid"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trials",
    )
    strategy_name = models.CharField(max_length=255)
    machine_id_snapshot = models.CharField(
        max_length=64,
        help_text="SHA-256 hash of machine ID at the time the trial started.",
        db_index=True,
    )
    started_at = models.DateTimeField(default=timezone.now)
    ends_at = models.DateTimeField(
        help_text="When this free trial ends.",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )
    deactivated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the trial was deactivated (expired or converted).",
    )

    class Meta:
        # Prevent duplicate trials for same user + strategy
        unique_together = [['user', 'strategy_name']]
        indexes = [
            models.Index(fields=['machine_id_snapshot', 'strategy_name']),
            models.Index(fields=['status', 'ends_at']),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.strategy_name} ({self.status})"

    @property
    def is_active(self) -> bool:
        """Check if trial is currently active."""
        return self.status == "active" and self.ends_at > timezone.now()
    
    @property
    def days_remaining(self) -> int:
        """Calculate days remaining in trial."""
        if self.status != "active":
            return 0
        delta = self.ends_at - timezone.now()
        return max(0, delta.days)

    def check_and_expire(self):
        """Check if trial has expired and update status if needed."""
        if self.status == "active" and self.ends_at <= timezone.now():
            self.status = "expired"
            self.deactivated_at = timezone.now()
            self.save(update_fields=['status', 'deactivated_at'])
            return True
        return False
    
    @classmethod
    def can_user_start_trial(cls, user, strategy_name: str) -> tuple[bool, str]:
        """
        Check if user can start a trial for the given strategy.
        
        Returns:
            (can_start: bool, reason: str)
        """
        # Check if user already has a trial for this strategy
        existing_trial = cls.objects.filter(
            user=user,
            strategy_name=strategy_name
        ).first()
        
        if existing_trial:
            return False, "You have already used your trial for this strategy"
        
        # Check if user has machine ID set
        if not user.has_machine_id:
            return False, "Please set your machine ID first"
        
        return True, "OK"


class TrialAbuseLog(models.Model):
    """
    Log all trial attempts to detect and prevent abuse.
    Tracks email + machine ID hash combinations.
    """
    
    email = models.EmailField(db_index=True)
    machine_id_hash = models.CharField(max_length=64, db_index=True)
    strategy_name = models.CharField(max_length=255)
    attempted_at = models.DateTimeField(default=timezone.now)
    blocked = models.BooleanField(
        default=False,
        help_text="Whether this attempt was blocked as suspicious"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['email', 'machine_id_hash']),
            models.Index(fields=['attempted_at']),
        ]
    
    def __str__(self) -> str:
        status = "BLOCKED" if self.blocked else "ALLOWED"
        return f"{status}: {self.email} - {self.strategy_name}"


class Subscription(models.Model):
    """
    Paid access record – rental or lifetime.
    These appear together with trials in the account section.
    """

    ACCESS_TYPE_CHOICES = [
        ("rental", "Monthly Rental"),
        ("lifetime", "Lifetime Purchase"),
        ("bundle", "Bundle Purchase"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("expired", "Expired"),
        ("cancelled", "Cancelled"),
        ("payment_failed", "Payment Failed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    strategy_name = models.CharField(
        max_length=255,
        help_text="Single strategy name, or 'Bundle' for multiple strategies"
    )
    bundle_strategies = models.JSONField(
        null=True,
        blank=True,
        help_text="List of strategy names if this is a bundle purchase"
    )
    access_type = models.CharField(
        max_length=20,
        choices=ACCESS_TYPE_CHOICES,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )
    started_at = models.DateTimeField(default=timezone.now)
    ends_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="For rentals only. Lifetime purchases can leave this empty.",
    )
    next_billing_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Next billing date for recurring subscriptions"
    )
    paypal_subscription_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="PayPal subscription ID for recurring payments",
    )
    paypal_plan_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="PayPal plan ID",
    )

    class Meta:
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'ends_at']),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.strategy_name} [{self.access_type}]"

    @property
    def is_active(self) -> bool:
        """Check if subscription is currently active."""
        if self.status != "active":
            return False
        if self.access_type == "lifetime":
            return True
        if self.ends_at:
            return self.ends_at > timezone.now()
        return True
    
    def handle_failed_payment(self):
        """Handle failed payment - immediate deactivation."""
        self.status = "payment_failed"
        self.save(update_fields=['status'])
    
    def cancel_subscription(self):
        """Cancel the subscription."""
        self.status = "cancelled"
        self.save(update_fields=['status'])


class PayPalPayment(models.Model):
    """
    Track all PayPal transactions for audit and reconciliation.
    """
    
    PAYMENT_TYPE_CHOICES = [
        ("subscription", "Subscription Payment"),
        ("one_time", "One-Time Payment"),
    ]
    
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="paypal_payments",
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )
    paypal_order_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="PayPal order/transaction ID"
    )
    paypal_subscription_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="PayPal subscription ID if applicable"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Payment amount"
    )
    currency = models.CharField(
        max_length=3,
        default="USD",
        help_text="Currency code (USD, EUR, etc.)"
    )
    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )
    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Store raw PayPal webhook data for debugging
    webhook_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Raw PayPal webhook payload"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['paypal_order_id']),
        ]
    
    def __str__(self) -> str:
        return f"{self.user.email} - ${self.amount} ({self.status})"
