import uuid
import random

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import random
import string

from .managers import CustomUserManager


class User(AbstractBaseUser, PermissionsMixin):
    pkid = models.BigAutoField(primary_key=True, editable=False)
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    username = models.CharField(
        verbose_name=_("username"),
        max_length=50,
        unique=True,
        db_index=True,
    )
    first_name = models.CharField(verbose_name=_("first name"), max_length=50, null=True, blank=True)
    last_name = models.CharField(verbose_name=_("last name"), max_length=50, null=True, blank=True)
    email = models.EmailField(
        verbose_name=_("email address"), db_index=True, unique=True
    )
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    # Social login fields for future use
    provider = models.CharField(max_length=50, blank=True, null=True)
    provider_id = models.CharField(max_length=100, blank=True, null=True)
    avatar_url = models.URLField(blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]
    objects = CustomUserManager()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self) -> str:
        return self.username

    # @property
    # def get_full_name(self):
    #     first = (self.first_name or "").title()
    #     last = (self.last_name or "").title()
    #     full_name = f"{first} {last}".strip()
    #     return full_name or self.username or self.email

    # @property
    # def get_short_name(self):
    #     return (self.first_name or self.username or self.email or "User").title()


class EmailVerificationCode(models.Model):
    CODE_TYPES = (
        ('registration', 'Registration'),
        ('password_reset', 'Password Reset'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    code_type = models.CharField(max_length=20, choices=CODE_TYPES)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'email_verification_codes'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.code} ({self.code_type})"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(minutes=15)
        super().save(*args, **kwargs)

    @staticmethod
    def generate_code():
        return ''.join(random.choices(string.digits, k=6))

    def is_expired(self):
        return timezone.now() > self.expires_at

    def is_valid(self):
        return not self.is_used and not self.is_expired()


