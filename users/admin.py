from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin configuration for CustomUser model."""
    
    model = CustomUser
    
    list_display = [
        'email',
        'first_name',
        'last_name',
        'email_verified',
        'has_machine_id',
        'subscription_status',
        'has_lifetime_access',
        'is_staff',
        'created_at',
    ]
    
    list_filter = [
        'email_verified',
        'subscription_status',
        'has_lifetime_access',
        'is_staff',
        'is_superuser',
        'is_active',
    ]
    
    search_fields = ['email', 'first_name', 'last_name']
    
    ordering = ['-created_at']
    
    readonly_fields = ['created_at', 'updated_at', 'machine_id_hash', 'machine_id_set_at', 'has_machine_id']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Email Verification', {
            'fields': ('email_verified', 'email_verification_token')
        }),
        ('Machine ID', {
            'fields': ('machine_id_hash', 'machine_id_set_at', 'has_machine_id'),
            'description': 'Machine ID is hashed for security. Users can only set it once.'
        }),
        ('Trading Info', {
            'fields': (
                'subscription_status',
                'subscription_end_date',
                'has_lifetime_access',
            )
        }),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
        ('Important Dates', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )

