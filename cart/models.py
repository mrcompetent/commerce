# cart/models.py
import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
from store.models import Product  # adjust import if your app is named differently


class Cart(models.Model):
    class CartStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        ORDERED = "ordered", "Ordered"
        ABANDONED = "abandoned", "Abandoned"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="carts",
    )
    # used for guests (we’ll store this in a cookie instead of session)
    anonymous_id = models.CharField(
        max_length=64, blank=True, null=True, db_index=True
    )

    status = models.CharField(
        max_length=20, choices=CartStatus.choices, default=CartStatus.ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        label = self.user or self.anonymous_id or self.pk
        return f"Cart({label})"
    
    def clear(self, set_status=None):
        """
        Remove all items from this cart.
        Optionally update status (e.g. after successful checkout).
        """
        # delete all related CartItem rows
        self.items.all().delete()

        if set_status is not None:
            self.status = set_status
            self.save(update_fields=["status"])
        else:
            # just touch updated_at if you use TimeStampedModel
            self.save(update_fields=["updated_at"])

    @property
    def items_qs(self):
        return self.items.select_related("product")

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items_qs)

    @property
    def total_amount(self):
        return sum(item.total_price for item in self.items_qs)


class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="cart_items"
    )
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("cart", "product")

    def __str__(self):
        return f"{self.product} × {self.quantity}"

    @property
    def total_price(self):
        return self.unit_price * self.quantity
