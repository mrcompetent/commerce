# store/views.py
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, ListView, DetailView
from .models import Category, Product, Color, Size
from wishlist.models import WishlistItem
from orders.models import Order 
from django.db.models import Sum, Q
from django.db.models import Min, Max, Count

class Home(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Top-level categories for “Shop by Category”
        ctx["home_categories"] = Category.objects.filter(
            is_active=True,
            parent__isnull=True
        ).order_by("name")

        # Featured products
        ctx["featured_products"] = Product.objects.filter(
            status=Product.ProductStatus.ACTIVE,
            is_featured=True,
        ).order_by("-created_at")[:8]

        # ✅ Popular products = best sellers from PAID orders (fallback to newest if none)
        popular_qs = (
            Product.objects
            .filter(status=Product.ProductStatus.ACTIVE)
            .annotate(
                sold_qty=Sum(
                    "orderitem__quantity",   # if you did NOT set related_name on OrderItem.product
                    filter=Q(orderitem__order__status=Order.Status.PAID),
                )
            )
            .filter(sold_qty__gt=0)
            .order_by("-sold_qty", "-id")[:8]
        )

        if not popular_qs.exists():
            popular_qs = Product.objects.filter(
                status=Product.ProductStatus.ACTIVE
            ).order_by("-created_at")[:8]

        ctx["popular_products"] = popular_qs
        return ctx
    
class CategoryListView(ListView):
    model = Category
    template_name = "category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        # top-level active categories only
        return (
            Category.objects
            .filter(is_active=True, parent__isnull=True)
            .prefetch_related("children")
            .order_by("name")
        )


class CategoryDetail(ListView):
    template_name = "category_detail.html"
    context_object_name = "products"
    paginate_by = 12

    def dispatch(self, request, *args, **kwargs):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs["slug"],
            is_active=True
        )
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        category_ids = [self.category.id] + list(
            self.category.children.values_list("id", flat=True)
        )

        qs = (
            Product.objects.filter(
                status=Product.ProductStatus.ACTIVE,
                category_id__in=category_ids
            )
            .select_related("category")
            .prefetch_related("colors", "sizes")
        )

        # ✅ filters
        selected_colors = self.request.GET.getlist("color")   # list of ids (strings)
        selected_sizes  = self.request.GET.getlist("size")

        min_price = self.request.GET.get("min_price")
        max_price = self.request.GET.get("max_price")

        if min_price:
            qs = qs.filter(price__gte=min_price)
        if max_price:
            qs = qs.filter(price__lte=max_price)

        # IMPORTANT:
        # "Any selected color" (OR) – product has at least one of the selected colors
        if selected_colors:
            qs = qs.filter(colors__id__in=selected_colors).distinct()

        if selected_sizes:
            qs = qs.filter(sizes__id__in=selected_sizes).distinct()

        # ✅ sorting
        sort = self.request.GET.get("sort", "default")
        if sort == "price_asc":
            qs = qs.order_by("price")
        elif sort == "price_desc":
            qs = qs.order_by("-price")
        elif sort == "newest":
            qs = qs.order_by("-created_at")
        else:
            qs = qs.order_by("name")

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx["category"] = self.category
        ctx["current_sort"] = self.request.GET.get("sort", "default")

        # keep selections in template
        ctx["selected_colors"] = set(self.request.GET.getlist("color"))
        ctx["selected_sizes"]  = set(self.request.GET.getlist("size"))
        ctx["min_price_value"] = self.request.GET.get("min_price", "")
        ctx["max_price_value"] = self.request.GET.get("max_price", "")

        # ✅ price bounds (based on category products BEFORE user price filter, or store-wide if you prefer)
        category_ids = [self.category.id] + list(
            self.category.children.values_list("id", flat=True)
        )
        base_qs = Product.objects.filter(
            status=Product.ProductStatus.ACTIVE,
            category_id__in=category_ids
        )
        ctx["min_price_bound"] = base_qs.aggregate(v=Min("price"))["v"] or 0
        ctx["max_price_bound"] = base_qs.aggregate(v=Max("price"))["v"] or 0

        # ✅ SHOW ALL COLORS + ALL SIZES store-wide (with counts of ACTIVE products)
        # Counts are store-wide. If you want counts within this category only, tell me.
        ctx["available_colors"] = (
            Color.objects
            .annotate(
                product_count=Count(
                    "products",
                    filter=Q(products__status=Product.ProductStatus.ACTIVE),
                    distinct=True
                )
            )
            .order_by("name")
        )

        ctx["available_sizes"] = (
            Size.objects
            .annotate(
                product_count=Count(
                    "products",
                    filter=Q(products__status=Product.ProductStatus.ACTIVE),
                    distinct=True
                )
            )
            .order_by("name")
        )

        return ctx
    


class ProductDetail(DetailView):
    model = Product
    template_name = "product_detail.html"
    context_object_name = "product"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        product = self.object

        # Build gallery image list (main + any extra ones that are set)
        images = [product.image_main]
        for img in [product.image_2, product.image_3, product.image_4, product.image_5]:
            if img:
                images.append(img)
        ctx["gallery_images"] = images

        # Featured products for the right sidebar
        ctx["featured_products"] = (
            Product.objects.filter(is_featured=True, status=Product.ProductStatus.ACTIVE)
            .exclude(pk=product.pk)[:3]
        )

        # Related products (same category)
        ctx["related_products"] = (
            Product.objects.filter(category=product.category, status=Product.ProductStatus.ACTIVE)
            .exclude(pk=product.pk)[:8]
        )

        ctx["is_in_wishlist"] = (
            self.request.user.is_authenticated
            and WishlistItem.objects.filter(user=self.request.user, product=product).exists()
        )

        return ctx
