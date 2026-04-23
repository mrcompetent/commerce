from django.urls import path
from . import views

urlpatterns = [
    path("", views.wishlist_view, name="wishlist"),
    path("wishlist/add/<uuid:product_id>/", views.add_to_wishlist, name="add_to_wishlist"),
    path("wishlist/remove/<uuid:product_id>/", views.remove_from_wishlist, name="remove_from_wishlist"),
    path("wishlist/add-to-cart/<uuid:product_id>/", views.wishlist_add_to_cart, name="wishlist_add_to_cart"),
]
