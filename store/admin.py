from django.contrib import admin
from .models import Category, Tag, Color, Size, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "is_active")
    list_filter = ("is_active",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ("name", "hex_code")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ("name", "label")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "category", "price", "status", "stock_quantity")
    list_filter = ("status", "category", "tags", "colors")
    search_fields = ("name", "sku")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("category", "tags", "colors", "sizes")
