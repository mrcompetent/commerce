# cart/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.cart_detail, name="cart_detail"),
    path("cart/add/<slug:slug>/", views.add_to_cart, name="add_to_cart"),
    path("cart/item/<uuid:item_id>/remove/", views.cart_item_remove, name="cart_item_remove"),
    path("cart/item/<uuid:item_id>/update/", views.cart_item_update, name="cart_item_update"),
    path("checkout/", views.checkout, name="checkout"),
    path("checkout/success/<int:order_id>/", views.checkout_success, name="checkout_success"),
    path("checkout/cancel/", views.checkout_cancel, name="checkout_cancel"),
    path("cart/buy-now/<uuid:product_id>/", views.buy_now, name="buy_now"),
]
