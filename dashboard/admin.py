from django.contrib import admin
from .models import Strategy, StrategyDownload


@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    """Admin configuration for Strategy model."""
    
    list_display = [
        'display_name',
        'name',
        'price_monthly',
        'price_lifetime',
        'is_active',
        'created_at',
    ]
    
    list_filter = [
        'is_active',
        'created_at',
    ]
    
    search_fields = [
        'name',
        'display_name',
        'description',
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    ordering = ['display_name']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'display_name', 'description', 'is_active')
        }),
        ('Pricing', {
            'fields': ('price_monthly', 'price_lifetime')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(StrategyDownload)
class StrategyDownloadAdmin(admin.ModelAdmin):
    """Admin configuration for StrategyDownload model."""
    
    list_display = [
        'user',
        'strategy',
        'access_type',
        'trial_triggered',
        'downloaded_at',
    ]
    
    list_filter = [
        'access_type',
        'trial_triggered',
        'downloaded_at',
    ]
    
    search_fields = [
        'user__email',
        'strategy__name',
        'strategy__display_name',
    ]
    
    readonly_fields = [
        'user',
        'strategy',
        'downloaded_at',
        'access_type',
        'machine_id_hash',
        'trial_triggered',
    ]
    
    ordering = ['-downloaded_at']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'strategy', 'access_type', 'trial_triggered')
        }),
        ('Download Info', {
            'fields': ('downloaded_at', 'machine_id_hash')
        }),
    )
