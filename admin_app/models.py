from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone

class UserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifier
    for authentication instead of usernames.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email address must be provided')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User Model utilizing email for authentication and JWT tokens.
    """
    ROLE_CHOICES = (
        ('ADMIN', 'Administrator'),
        ('STAFF', 'Staff Member'),
        ('CONSULTANT', 'Consultant'),
        ('COUNSELOR', 'Counselor'),
        ('USER', 'General User / Student'),
    )

    email = models.EmailField(unique=True, db_index=True, verbose_name="Email Address")
    first_name = models.CharField(max_length=150, blank=True, verbose_name="First Name")
    last_name = models.CharField(max_length=150, blank=True, verbose_name="Last Name")
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Phone Number")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='USER', verbose_name="User Role")

    is_active = models.BooleanField(default=True, verbose_name="Active")
    is_staff = models.BooleanField(default=False, verbose_name="Staff Status")
    is_superuser = models.BooleanField(default=False, verbose_name="Superuser Status")

    date_joined = models.DateTimeField(default=timezone.now, verbose_name="Date Joined")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Last Updated")

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.email

    @property
    def get_full_name(self):
        full = f"{self.first_name} {self.last_name}".strip()
        return full if full else self.email


class AdminAuditLog(models.Model):
    """
    Logs administrative actions for auditing purposes.
    """
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'

    def __str__(self):
        return f"{self.action} by {self.actor or 'System'} at {self.created_at}"


class SiteSetting(models.Model):
    """
    Key-value dynamic site configurations manageable by admin.
    """
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField(blank=True)
    description = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.key


def generate_unique_referral_code(prefix="EDU"):
    import random
    import string
    chars = string.ascii_uppercase + string.digits
    suffix = ''.join(random.choices(chars, k=6))
    return f"{prefix}-{suffix}"


class Consultant(models.Model):
    """
    Consultant profile linked to User account.
    Stores auto-generated referral code and link, tracking student leads.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='consultant_profile'
    )
    referral_code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name="Referral Code"
    )
    agency_name = models.CharField(max_length=150, blank=True, verbose_name="Agency / Organization")
    city = models.CharField(max_length=100, blank=True, verbose_name="City")
    is_active = models.BooleanField(default=True, verbose_name="Active Status")
    notes = models.TextField(blank=True, verbose_name="Internal Notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Consultant'
        verbose_name_plural = 'Consultants'

    def __str__(self):
        return f"{self.user.get_full_name} ({self.referral_code})"

    def save(self, *args, **kwargs):
        if not self.referral_code:
            code = generate_unique_referral_code()
            while Consultant.objects.filter(referral_code=code).exists():
                code = generate_unique_referral_code()
            self.referral_code = code
        super().save(*args, **kwargs)

    def get_referral_link(self, request=None):
        from django.conf import settings
        frontend_base = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        return f"{frontend_base}/?ref={self.referral_code}"

    @property
    def total_leads(self):
        return self.user.assigned_leads.count()

    @property
    def new_leads(self):
        return self.user.assigned_leads.filter(status='NEW').count()

    @property
    def enrolled_leads(self):
        return self.user.assigned_leads.filter(status='ENROLLED').count()
