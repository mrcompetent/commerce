# cart/utils.py
from .models import Cart
import uuid

COOKIE_NAME = "cart_id"
COOKIE_AGE = 60 * 60 * 24 * 30

def get_cart_for_request(request):
    if request.user.is_authenticated:
        return (
            Cart.objects
            .filter(user=request.user, status=Cart.CartStatus.ACTIVE)
            .prefetch_related("items__product")
            .first()
        )

    anon_id = request.COOKIES.get(COOKIE_NAME)
    if not anon_id:
        return None

    return (
        Cart.objects
        .filter(anonymous_id=anon_id, user__isnull=True, status=Cart.CartStatus.ACTIVE)
        .prefetch_related("items__product")
        .first()
    )


def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(
            user=request.user,
            status=Cart.CartStatus.ACTIVE,
        )
        return cart

    anon_id = request.COOKIES.get(COOKIE_NAME)
    if anon_id:
        cart = Cart.objects.filter(
            anonymous_id=anon_id,
            user__isnull=True,
            status=Cart.CartStatus.ACTIVE,
        ).first()
        if cart:
            return cart

    anon_id = uuid.uuid4().hex
    cart = Cart.objects.create(anonymous_id=anon_id, status=Cart.CartStatus.ACTIVE)
    request.cart_cookie_to_set = anon_id
    return cart


from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone


def send_order_paid_emails(*, order, items, user):
    brand_name = getattr(settings, "BRAND_NAME", "Porto eCommerce Clone")
    year = timezone.now().year

    ctx = {
        "order": order,
        "items": items,
        "user": user,
        "brand_name": brand_name,
        "year": year,
    }

    # ✅ Customer email
    subject_customer = f"Order #{order.id} confirmed"
    to_customer = [user.email]
    from_email = settings.DEFAULT_FROM_EMAIL

    text_customer = render_to_string("order_paid_customer.txt", ctx)
    html_customer = render_to_string("order_paid_customer.html", ctx)

    msg_customer = EmailMultiAlternatives(
        subject_customer,
        text_customer,
        from_email,
        to_customer,
        reply_to=[from_email],
    )
    msg_customer.attach_alternative(html_customer, "text/html")

    # ✅ Admin email
    subject_admin = f"NEW PAID ORDER #{order.id} - {user.username}"
    admin_email = getattr(settings, "SUPPORT_EMAIL", settings.DEFAULT_FROM_EMAIL)
    to_admin = [admin_email]

    text_admin = render_to_string("order_paid_admin.txt", ctx)
    html_admin = render_to_string("order_paid_admin.html", ctx)

    msg_admin = EmailMultiAlternatives(
        subject_admin,
        text_admin,
        from_email,
        to_admin,
        reply_to=[user.email],  # admin can reply to customer directly
    )
    msg_admin.attach_alternative(html_admin, "text/html")

    # send both
    msg_customer.send()
    msg_admin.send()
