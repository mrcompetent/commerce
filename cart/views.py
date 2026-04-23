# cart/views.py
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from accounts.models import Address 
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.contrib import messages
import stripe
from django.http import JsonResponse, HttpResponseRedirect
from store.models import Product
from .cart import Cart

from orders.models import Order, OrderItem

# cart/views.py
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .utils import send_order_paid_emails
from store.models import Product
from .models import CartItem, Cart
from .utils import get_or_create_cart, get_cart_for_request, COOKIE_NAME, COOKIE_AGE


def _attach_cart_cookie_if_needed(request, response):
    anon_id = getattr(request, "cart_cookie_to_set", None)
    if anon_id:
        response.set_cookie(COOKIE_NAME, anon_id, max_age=COOKIE_AGE, httponly=True)
    return response


@login_required
def cart_detail(request):
    cart = get_or_create_cart(request)

    default_address = (
        Address.objects
        .filter(
            user=request.user,
            is_default=True,
            address_type=Address.AddressType.SHIPPING,
        )
        .first()
    )

    return render(request, "cart.html", {
        "cart": cart,
        "default_address": default_address,
    })


def _is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"

@login_required
@require_POST
def add_to_cart(request, slug):
    # 1) find product by slug
    product = get_object_or_404(
        Product,
        slug=slug,
        status=Product.ProductStatus.ACTIVE,
    )

    # 2) quantity from POST
    try:
        qty = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        qty = 1
    if qty < 1:
        qty = 1

    # 3) get/create OPEN cart (DB-backed, user or anonymous)
    cart = get_or_create_cart(request)

    # 4) get/create cart item
    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={"unit_price": product.price},
    )

    if created:
        item.quantity = qty       # first time → set to qty
    else:
        item.quantity += qty      # already exists → increment

    item.save(update_fields=["quantity"])

    if _is_ajax(request):
        return JsonResponse({
            "ok": True,
            "message": "Successfully added to cart.",
            "cart_count": cart.item_count,
            "cart_total": str(cart.total_amount),
        })

    # Non-AJAX fallback (normal behavior)
    messages.success(request, "Successfully added to cart.")
    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))


@require_POST
def cart_item_update(request, item_id):
    """
    Handles + / - / set quantity via 'action' POST field.
    """
    cart = get_cart_for_request(request) or get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)

    action = request.POST.get("action")

    if action == "inc":
        item.quantity += 1
        item.save(update_fields=["quantity"])

    elif action == "dec":
        item.quantity -= 1
        if item.quantity <= 0:
            item.delete()
        else:
            item.save(update_fields=["quantity"])

    elif action == "set":
        try:
            qty = int(request.POST.get("quantity", item.quantity))
        except (TypeError, ValueError):
            qty = item.quantity
        if qty <= 0:
            item.delete()
        else:
            item.quantity = qty
            item.save(update_fields=["quantity"])

    response = redirect("cart_detail")
    return _attach_cart_cookie_if_needed(request, response)


@require_POST
def cart_item_remove(request, item_id):
    cart = get_cart_for_request(request) or get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.delete()
    response = redirect("cart_detail")
    return _attach_cart_cookie_if_needed(request, response)


@login_required
@require_POST
def buy_now(request, product_id):
    # 1) find product by UUID
    product = get_object_or_404(
        Product,
        id=product_id,
        status=Product.ProductStatus.ACTIVE,
    )

    # 2) quantity from POST
    try:
        qty = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        qty = 1
    qty = max(1, qty)

    # 3) get/create cart
    cart = get_or_create_cart(request)

    # 5) create the one cart item
    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={"unit_price": product.price, "quantity": qty},
    )
    if not created:
        item.quantity += qty
        item.save(update_fields=["quantity"])

    # 6) redirect to checkout
    response = redirect("checkout")
    return _attach_cart_cookie_if_needed(request, response)



@login_required
def checkout(request):
    cart = get_cart_for_request(request) or get_or_create_cart(request)

    default_address = (
        Address.objects
        .filter(
            user=request.user,
            is_default=True,
            address_type=Address.AddressType.SHIPPING,
        )
        .first()
    )

    if not cart or cart.item_count == 0:
        return redirect("cart_detail")

    if request.method == "POST":
        if not default_address:
            # keep your UX choice; this is the safest
            return redirect("addresses")

        stripe.api_key = settings.STRIPE_SECRET_KEY

        # ✅ 1) CREATE ORDER (PENDING) BEFORE STRIPE
        order = Order.objects.create(
            user=request.user,
            status=Order.Status.PENDING,
            subtotal=cart.total_amount,
            total=cart.total_amount,
            currency="USD",

            shipping_full_name=default_address.full_name,
            shipping_line1=default_address.line1,
            shipping_line2=default_address.line2 or "",
            shipping_city=default_address.city,
            shipping_state=default_address.state or "",
            shipping_postal_code=default_address.postal_code or "",
            shipping_country=default_address.country,
            shipping_phone=default_address.phone or "",
        )

        # ✅ 2) COPY CART ITEMS → ORDER ITEMS
        for item in cart.items_qs.select_related("product"):
            OrderItem.objects.create(
                order=order,
                product=item.product,
                name=item.product.name,
                unit_price=item.unit_price,
                quantity=item.quantity,
            )

        # ✅ 3) BUILD STRIPE LINE ITEMS (same as you already do)
        line_items = []
        for item in cart.items_qs:
            price_cents = int((item.unit_price * Decimal("100")).quantize(Decimal("1")))
            line_items.append({
                "price_data": {
                    "currency": "usd",
                    "unit_amount": price_cents,
                    "product_data": {"name": item.product.name},
                },
                "quantity": item.quantity,
            })

        domain = request.build_absolute_uri("/").rstrip("/")

        # ✅ 4) SUCCESS URL MUST INCLUDE order_id
        success_url = domain + reverse("checkout_success", kwargs={"order_id": order.id})
        cancel_url  = domain + reverse("checkout_cancel")

        # ✅ 5) CREATE STRIPE SESSION + STORE session id on the order
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=line_items,
            success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            metadata={
                "order_id": str(order.id),
                "user_id": str(request.user.id),
                "cart_id": str(cart.id),
            },
        )

        order.stripe_session_id = session.id
        order.save(update_fields=["stripe_session_id"])

        response = redirect(session.url)
        return _attach_cart_cookie_if_needed(request, response)

    context = {
        "cart": cart,
        "default_address": default_address,
        "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
    }
    response = render(request, "checkout.html", context)
    return _attach_cart_cookie_if_needed(request, response)



@login_required
def checkout_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    session_id = request.GET.get("session_id")
    if session_id and order.stripe_session_id and session_id == order.stripe_session_id:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status == "paid" and order.status != Order.Status.PAID:
            order.status = Order.Status.PAID
            order.stripe_payment_intent = session.payment_intent or ""
            order.save(update_fields=["status", "stripe_payment_intent"])

            # close cart
            cart = get_or_create_cart(request)
            cart.status = "ordered"  # change to your CartStatus value
            cart.save(update_fields=["status"])

            # ✅ SEND EMAILS (customer + admin)
            items = order.items.select_related("product").all()
            send_order_paid_emails(order=order, items=items, user=request.user)

    return render(request, "checkout_success.html", {
        "order": order,
        "items": order.items.select_related("product").all(),
    })

@login_required
def checkout_cancel(request):
    return render(request, "checkout_cancel.html")
