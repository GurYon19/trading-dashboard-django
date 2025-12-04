from django.db import models
from django.conf import settings
from django.utils import timezone


class Strategy(models.Model):
    """
    Trading strategy available for purchase/rental.
    """
    
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Internal strategy identifier (e.g., 'momentum_v1')"
    )
    display_name = models.CharField(
        max_length=255,
        help_text="User-friendly name shown in UI"
    )
    description = models.TextField(
        help_text="Strategy description and details"
    )
    price_monthly = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Monthly rental price (null if not available)"
    )
    price_lifetime = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="One-time lifetime purchase price (null if not available)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this strategy is available for purchase"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Strategies"
        ordering = ['display_name']
    
    def __str__(self):
        return self.display_name


class StrategyDownload(models.Model):
    """
    Track all strategy downloads for analytics and trial triggering.
    """
    
    ACCESS_TYPE_CHOICES = [
        ('trial', 'Trial'),
        ('subscription', 'Subscription'),
        ('lifetime', 'Lifetime'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='strategy_downloads'
    )
    strategy = models.ForeignKey(
        Strategy,
        on_delete=models.CASCADE,
        related_name='downloads'
    )
    downloaded_at = models.DateTimeField(default=timezone.now)
    access_type = models.CharField(
        max_length=20,
        choices=ACCESS_TYPE_CHOICES,
        help_text="Type of access at download time"
    )
    machine_id_hash = models.CharField(
        max_length=64,
        help_text="Machine ID hash at download time"
    )
    trial_triggered = models.BooleanField(
        default=False,
        help_text="Whether this download triggered a trial"
    )
    
    class Meta:
        ordering = ['-downloaded_at']
        indexes = [
            models.Index(fields=['user', 'strategy']),
            models.Index(fields=['downloaded_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.strategy.display_name} ({self.access_type})"
