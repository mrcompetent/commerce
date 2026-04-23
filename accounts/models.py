from django.conf import settings
from django.db import models
import secrets
from datetime import timedelta
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone


# accounts/models.py
import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
from datetime import timedelta

from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email_verified = models.BooleanField(default=False)


class EmailOTP(models.Model):
    PURPOSE_CHOICES = (
        ("register", "Register"),
        ("login", "Login"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="email_otps")
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def create_for_user(cls, user, purpose, minutes_valid=10):
        code = str(uuid.uuid4().int)[0:6]
        otp = cls.objects.create(
            user=user,
            code=code,
            purpose=purpose,
            expires_at=timezone.now() + timedelta(minutes=minutes_valid),
        )
        return otp, code

    def is_valid(self):
        return (not self.is_used) and timezone.now() <= self.expires_at
# accounts/models.py (or custom user model)




class Address(models.Model):
    class AddressType(models.TextChoices):
        SHIPPING = "shipping", "Shipping"
        BILLING = "billing", "Billing"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="addresses",
    )
    full_name = models.CharField(max_length=255)
    line1 = models.CharField("Address line 1", max_length=255)
    line2 = models.CharField(
        "Address line 2",
        max_length=255,
        blank=True,
    )
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default="USA")

    phone = models.CharField(max_length=30, blank=True)

    address_type = models.CharField(
        max_length=20,
        choices=AddressType.choices,
        default=AddressType.SHIPPING,
    )

    is_default = models.BooleanField(
        default=False,
        help_text="Default shipping address.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        return f"{self.full_name} – {self.line1}, {self.city}"
