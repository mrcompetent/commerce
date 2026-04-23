import uuid

from django.db import models
from django.urls import reverse

from cloudinary.models import CloudinaryField


class TimeStampedModel(models.Model):
    """Abstract base with created/updated timestamps."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(TimeStampedModel):
    """
    Product categories (e.g. Shoes, Bags, Electronics).
    Supports simple nesting via parent.
    """
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=160, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )
    image = CloudinaryField(
        "category_image",
        blank=True,
        null=True,
        help_text="Optional image used in category banners / thumbnails.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self):
        return reverse("category_detail", args=[self.slug])


class Tag(TimeStampedModel):
    """Simple tag for products (e.g. Clothes, Fashion)."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Color(models.Model):
    """
    Color options. Hex code lets you render the swatches.
    """
    name = models.CharField(max_length=50, unique=True)  # e.g. "Black"
    slug = models.SlugField(max_length=60, unique=True)
    hex_code = models.CharField(
        max_length=7,
        default="#000000",
        help_text="Hex color like #000000",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Size(models.Model):
    """
    Size options (for shoes / clothes).
    Keep it generic so you can reuse (S, M, L, 39, 40, etc.).
    """
    name = models.CharField(max_length=50, unique=True)  # e.g. "Medium"
    slug = models.SlugField(max_length=60, unique=True)
    label = models.CharField(
        max_length=20,
        help_text="Label shown to users (e.g. 'M', '39', 'XL').",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.label or self.name


class Product(TimeStampedModel):
    """
    Main product model.

    Designed to match your product detail page:
    - 1–5 images (Cloudinary)
    - Name, slug, SKU
    - Short description + full description
    - Price + optional compare/sale price
    - Category, tags, colors, sizes
    - Stock / status
    """

    class ProductStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        DISCONTINUED = "discontinued", "Discontinued"

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=265, unique=True)
    sku = models.CharField(
        max_length=64,
        unique=True,
        help_text="Internal stock keeping unit.",
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    tags = models.ManyToManyField(
        Tag,
        related_name="products",
        blank=True,
    )

    # Descriptions
    short_description = models.CharField(
        max_length=300,
        blank=True,
        help_text="Shown near the price on the product page.",
    )
    description = models.TextField(
        blank=True,
        help_text="Full description / long text.",
    )

    # Pricing
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Current selling price.",
    )
    compare_at_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Original / strike-through price (optional).",
    )
    currency = models.CharField(
        max_length=3,
        default="USD",
        help_text="Currency code (e.g. USD, EUR, GBP).",
    )

    # Inventory
    stock_quantity = models.PositiveIntegerField(default=0)
    allow_backorder = models.BooleanField(
        default=False,
        help_text="Allow ordering when stock is zero.",
    )

    status = models.CharField(
        max_length=20,
        choices=ProductStatus.choices,
        default=ProductStatus.ACTIVE,
    )

    # Options
    colors = models.ManyToManyField(
        Color,
        related_name="products",
        blank=True,
    )
    sizes = models.ManyToManyField(
        Size,
        related_name="products",
        blank=True,
    )

    # Images (1–5) using Cloudinary
    image_main = CloudinaryField("product_image_main")
    image_2 = CloudinaryField(
        "product_image_2",
        blank=True,
        null=True,
    )
    image_3 = CloudinaryField(
        "product_image_3",
        blank=True,
        null=True,
    )
    image_4 = CloudinaryField(
        "product_image_4",
        blank=True,
        null=True,
    )
    image_5 = CloudinaryField(
        "product_image_5",
        blank=True,
        null=True,
    )

    is_featured = models.BooleanField(
        default=False,
        help_text="Show in featured sections / home page.",
    )

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["status"]),
            models.Index(fields=["category", "status"]),
        ]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self):
        return reverse("product_detail", args=[self.slug])

    @property
    def in_stock(self) -> bool:
        if self.stock_quantity > 0:
            return True
        return self.allow_backorder

    @property
    def display_price(self):
        """
        Helper for templates if you ever need to show
        price + compare_at_price together.
        """
        return self.price



