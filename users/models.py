from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
import hashlib
import secrets


class CustomUserManager(BaseUserManager):
    """Custom user manager where email is the unique identifier."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a user with the given email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('email_verified', True)  # Auto-verify superuser emails
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Custom user model for the trading dashboard.
    Uses email as the primary identifier instead of username.
    """
    
    SUBSCRIPTION_STATUS_CHOICES = [
        ('free', 'Free'),
        ('active', 'Active'),
        ('expired', 'Expired'),
    ]
    
    # Override email to make it unique and required
    email = models.EmailField(_('email address'), unique=True)
    
    # Email verification
    email_verified = models.BooleanField(
        default=False,
        help_text="Whether the user's email has been verified"
    )
    email_verification_token = models.CharField(
        max_length=64,
        blank=True,
        help_text="Token for email verification"
    )
    
    # Machine ID (hashed for security)
    machine_id_hash = models.CharField(
        max_length=64,
        blank=True,
        db_index=True,
        help_text="SHA-256 hash of machine ID for strategy activation"
    )
    machine_id_set_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the machine ID was registered"
    )
    
    # Legacy subscription fields (kept for backward compatibility)
    subscription_status = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_STATUS_CHOICES,
        default='free',
        help_text="Current subscription status"
    )
    
    subscription_end_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the subscription expires"
    )
    
    has_lifetime_access = models.BooleanField(
        default=False,
        help_text="User has purchased lifetime access"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Use email as the username field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Email is already required by USERNAME_FIELD
    
    objects = CustomUserManager()
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
    
    def __str__(self):
        return self.email
    
    def generate_verification_token(self):
        """Generate a secure email verification token."""
        self.email_verification_token = secrets.token_urlsafe(32)
        return self.email_verification_token
    
    def set_machine_id(self, machine_id: str) -> bool:
        """
        Set the machine ID for this user (can only be set once).
        
        Args:
            machine_id: The plain text machine ID
            
        Returns:
            True if successful, False if machine ID already set
        """
        if self.machine_id_hash:
            return False  # Machine ID already set, cannot change
        
        from django.utils import timezone
        self.machine_id_hash = hashlib.sha256(machine_id.encode()).hexdigest()
        self.machine_id_set_at = timezone.now()
        self.save(update_fields=['machine_id_hash', 'machine_id_set_at'])
        return True
    
    def verify_machine_id(self, machine_id: str) -> bool:
        """
        Verify if the provided machine ID matches the stored hash.
        
        Args:
            machine_id: The plain text machine ID to verify
            
        Returns:
            True if matches, False otherwise
        """
        if not self.machine_id_hash:
            return False
        
        provided_hash = hashlib.sha256(machine_id.encode()).hexdigest()
        return self.machine_id_hash == provided_hash
    
    @property
    def has_machine_id(self) -> bool:
        """Check if user has registered a machine ID."""
        return bool(self.machine_id_hash)
    
    @property
    def is_subscribed(self):
        """Check if user has an active subscription or lifetime access."""
        if self.has_lifetime_access:
            return True
        if self.subscription_status == 'active' and self.subscription_end_date:
            from django.utils import timezone
            return self.subscription_end_date > timezone.now()
        return False

