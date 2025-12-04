from django.contrib import admin
from .models import Trial, TrialAbuseLog, Subscription, PayPalPayment


@admin.register(Trial)
class TrialAdmin(admin.ModelAdmin):
    """Admin configuration for Trial model."""
    
    list_display = [
        'user',
        'strategy_name',
        'status',
        'started_at',
        'ends_at',
        'days_remaining',
    ]
    
    list_filter = [
        'status',
        'started_at',
        'ends_at',
    ]
    
    search_fields = [
        'user__email',
        'strategy_name',
        'machine_id_snapshot',
    ]
    
    readonly_fields = [
        'started_at',
        'deactivated_at',
        'days_remaining',
    ]
    
    ordering = ['-started_at']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'strategy_name', 'status')
        }),
        ('Trial Period', {
            'fields': ('started_at', 'ends_at', 'days_remaining', 'deactivated_at')
        }),
        ('Security', {
            'fields': ('machine_id_snapshot',)
        }),
    )


@admin.register(TrialAbuseLog)
class TrialAbuseLogAdmin(admin.ModelAdmin):
    """Admin configuration for TrialAbuseLog model."""
    
    list_display = [
        'email',
        'strategy_name',
        'blocked',
        'attempted_at',
    ]
    
    list_filter = [
        'blocked',
        'attempted_at',
    ]
    
    search_fields = [
        'email',
        'machine_id_hash',
        'strategy_name',
    ]
    
    readonly_fields = [
        'email',
        'machine_id_hash',
        'strategy_name',
        'attempted_at',
        'user',
    ]
    
    ordering = ['-attempted_at']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Admin configuration for Subscription model."""
    
    list_display = [
        'user',
        'strategy_name',
        'access_type',
        'status',
        'started_at',
        'ends_at',
    ]
    
    list_filter = [
        'access_type',
        'status',
        'started_at',
    ]
    
    search_fields = [
        'user__email',
        'strategy_name',
        'paypal_subscription_id',
    ]
    
    readonly_fields = [
        'started_at',
    ]
    
    ordering = ['-started_at']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'strategy_name', 'access_type', 'status')
        }),
        ('Bundle Info', {
            'fields': ('bundle_strategies',),
            'classes': ('collapse',),
        }),
        ('Subscription Period', {
            'fields': ('started_at', 'ends_at', 'next_billing_date')
        }),
        ('PayPal Info', {
            'fields': ('paypal_subscription_id', 'paypal_plan_id')
        }),
    )


@admin.register(PayPalPayment)
class PayPalPaymentAdmin(admin.ModelAdmin):
    """Admin configuration for PayPalPayment model."""
    
    list_display = [
        'user',
        'amount',
        'currency',
        'payment_type',
        'status',
        'created_at',
    ]
    
    list_filter = [
        'payment_type',
        'status',
        'currency',
        'created_at',
    ]
    
    search_fields = [
        'user__email',
        'paypal_order_id',
        'paypal_subscription_id',
    ]
    
    readonly_fields = [
        'created_at',
        'completed_at',
        'webhook_data',
    ]
    
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'subscription', 'status')
        }),
        ('Payment Info', {
            'fields': ('amount', 'currency', 'payment_type')
        }),
        ('PayPal Details', {
            'fields': ('paypal_order_id', 'paypal_subscription_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at')
        }),
        ('Debug Info', {
            'fields': ('webhook_data',),
            'classes': ('collapse',),
        }),
    )
