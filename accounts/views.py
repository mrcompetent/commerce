from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from wishlist.models import WishlistItem

from django.contrib.auth import get_user_model
from .forms import RegisterForm, LoginForm, AddressForm
from .models import Address
from orders.models import Order  # we'll add this in step 4


# accounts/views.py
from .forms import PasswordChangeInlineForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .forms import RegisterForm, LoginForm, OTPVerifyForm
from .models import EmailOTP, User
from .utils import send_otp_email
User = get_user_model()


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email_verified = False
            user.is_active = True
            user.save()

            otp, code = EmailOTP.create_for_user(user, purpose="register", minutes_valid=10)
            send_otp_email(user.email, code, username=user.username, minutes_valid=10)

            request.session["otp_user_id"] = str(user.id)
            request.session["otp_purpose"] = "register"

            messages.info(request, "We sent a verification code to your email.")
            return redirect("verify_email")
    else:
        form = RegisterForm()

    return render(request, "register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()

            if not user.email_verified:
                otp, code = EmailOTP.create_for_user(user, purpose="login", minutes_valid=10)
                send_otp_email(user.email, code, username=user.username, minutes_valid=10)

                request.session["otp_user_id"] = str(user.id)
                request.session["otp_purpose"] = "login"

                messages.warning(request, "Email not verified. Enter the code sent to your email.")
                return redirect("verify_email")

            login(request, user)
            return redirect("dashboard")
    else:
        form = LoginForm(request)

    return render(request, "login.html", {"form": form})


def verify_email_view(request):
    user_id = request.session.get("otp_user_id")
    purpose = request.session.get("otp_purpose")

    if not user_id or not purpose:
        messages.error(request, "Verification session expired. Please login again.")
        return redirect("login")

    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = OTPVerifyForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]

            otp = EmailOTP.objects.filter(
                user=user, code=code, purpose=purpose, is_used=False
            ).first()

            if not otp or not otp.is_valid():
                messages.error(request, "Invalid or expired code.")
            else:
                otp.is_used = True
                otp.save(update_fields=["is_used"])

                user.email_verified = True
                user.save(update_fields=["email_verified"])

                login(request, user)

                request.session.pop("otp_user_id", None)
                request.session.pop("otp_purpose", None)

                messages.success(request, "Email verified successfully.")
                return redirect("dashboard")
    else:
        form = OTPVerifyForm()

    return render(request, "verify_otp.html", {"form": form, "purpose": purpose})


def resend_verify_email(request):
    user_id = request.session.get("otp_user_id")
    purpose = request.session.get("otp_purpose")

    if not user_id or not purpose:
        messages.error(request, "Verification session expired. Please login again.")
        return redirect("login")

    user = get_object_or_404(User, id=user_id)

    otp, code = EmailOTP.create_for_user(user, purpose=purpose, minutes_valid=10)
    send_otp_email(user.email, code, username=user.username, minutes_valid=10)

    messages.info(request, "A new verification code has been sent.")
    return redirect("verify_email")


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")




@login_required
def dashboard_view(request):
    user = request.user
    if not request.user.email_verified:
        messages.warning(request, "Please verify your email first.")
        return redirect("verify_email")

    orders_qs = (
        Order.objects
        .filter(user=user)
        .prefetch_related("items__product")   # ✅ needed for images/items
        .order_by("-created_at")
    )

    total_orders = orders_qs.count()
    active_orders = orders_qs.filter(
        status__in=[Order.Status.PENDING, Order.Status.PAID]
    ).count()

    recent_orders = list(orders_qs[:5])

    wishlist_qs = WishlistItem.objects.filter(user=user).select_related("product")
    wishlist_count = wishlist_qs.count()
    wishlist_preview = list(wishlist_qs[:4])

    member_since_year = user.date_joined.year if user.date_joined else None

    context = {
        "total_orders": total_orders,
        "active_orders": active_orders,
        "recent_orders": recent_orders,
        "wishlist_count": wishlist_count,
        "wishlist_preview": wishlist_preview,
        "member_since_year": member_since_year,
    }
    return render(request, "dashboard.html", context)


@login_required
def address_list_create_view(request):
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address: Address = form.save(commit=False)
            address.user = request.user

            if address.is_default:
                # unset previous default
                Address.objects.filter(user=request.user, is_default=True).update(
                    is_default=False
                )

            address.save()
            messages.success(request, "Address saved.")
            return redirect("addresses")
    else:
        form = AddressForm()

    addresses = Address.objects.filter(user=request.user)
    return render(
        request,
        "addresses.html",
        {"form": form, "addresses": addresses},
    )


@login_required
def set_default_address_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)

    Address.objects.filter(user=request.user, is_default=True).update(
        is_default=False
    )
    address.is_default = True
    address.save(update_fields=["is_default"])

    messages.success(request, "Default address updated.")
    return redirect("addresses")


@login_required
def delete_address_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.delete()
    messages.info(request, "Address removed.")
    return redirect("addresses")


@login_required
def orders_list_view(request):
    orders = (
        Order.objects
        .filter(user=request.user)
        .prefetch_related("items__product")
        .order_by("-created_at")
    )

    return render(request, "orders.html", {
        "orders": orders,
        "active_tab": "orders",
    })


@login_required
def order_detail_view(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    items = order.items.select_related("product")
    return render(request, "order_detail.html", {"order": order, "items": items})



@login_required
def change_password_view(request):
    if request.method == "POST":
        form = PasswordChangeInlineForm(request.user, request.POST)
        if form.is_valid():
            new_password = form.cleaned_data["new_password1"]
            request.user.set_password(new_password)
            request.user.save()

            # keep user logged in
            update_session_auth_hash(request, request.user)

            messages.success(request, "Password updated successfully.")
            return redirect("dashboard")  # or "dashboard" or "change_password"
    else:
        form = PasswordChangeInlineForm(request.user)

    return render(request, "change_password.html", {"form": form})


from django.contrib.auth.views import PasswordResetConfirmView
from django.urls import reverse_lazy
from .forms import SetPasswordStyledForm

class PasswordResetConfirmCustomView(PasswordResetConfirmView):
    template_name = "password_reset_confirm.html"
    form_class = SetPasswordStyledForm
    success_url = reverse_lazy("password_reset_complete")