# wishlist/models.py
from django.conf import settings
from django.db import models
from store.models import Product

User = settings.AUTH_USER_MODEL


class WishlistItem(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="wishlist_items"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="wishlisted_in"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} → {self.product.name}"