from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.http import require_POST

from store.models import Product
from cart.models import CartItem
from cart.utils import get_or_create_cart
from .models import WishlistItem


def _is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def _redirect_back(request, fallback="/"):
    return HttpResponseRedirect(request.META.get("HTTP_REFERER", fallback))


@login_required
def wishlist_view(request):
    items = (
        WishlistItem.objects
        .filter(user=request.user)
        .select_related("product", "product__category")
    )
    return render(request, "wishlist.html", {"items": items})


@login_required
@require_POST
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    obj, created = WishlistItem.objects.get_or_create(
        user=request.user,
        product=product,
    )

    if _is_ajax(request):
        return JsonResponse({
            "ok": True,
            "action": "added",
            "created": created,
            "product_id": str(product.id),
        })

    return _redirect_back(request, fallback="/")


@login_required
@require_POST
def remove_from_wishlist(request, product_id):
    deleted, _ = WishlistItem.objects.filter(
        user=request.user,
        product_id=product_id,
    ).delete()

    if _is_ajax(request):
        return JsonResponse({
            "ok": True,
            "action": "removed",
            "deleted": deleted,
            "product_id": str(product_id),
        })

    # if user removed from wishlist page, keep redirect("wishlist")
    referer = request.META.get("HTTP_REFERER", "")
    if "/wishlist" in referer:
        return redirect("wishlist")

    return _redirect_back(request, fallback="/")


@login_required
@require_POST
def wishlist_add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_or_create_cart(request)

    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={"unit_price": product.price, "quantity": 1},
    )

    if not created:
        item.quantity += 1
        item.save(update_fields=["quantity"])

    # optional: remove from wishlist after adding to cart
    WishlistItem.objects.filter(user=request.user, product=product).delete()

    return redirect("cart_detail")
