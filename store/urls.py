# store/urls.py
from django.urls import path
from .views import Home, CategoryDetail, ProductDetail, CategoryListView

urlpatterns = [
    path("", Home.as_view(), name="home"),

    path("categories/", CategoryListView.as_view(), name="category_list"),

    path("category/<slug:slug>/", 
         CategoryDetail.as_view(), 
         name="category_detail"),

    path("product/<slug:slug>/",
         ProductDetail.as_view(),
         name="product_detail"),
]
