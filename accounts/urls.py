from django.urls import path, reverse_lazy
from . import views
from .views import PasswordResetConfirmCustomView
from django.contrib.auth import views as auth_views
from .forms import StyledPasswordResetForm

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("verify-email/", views.verify_email_view, name="verify_email"),
    path("verify-email/resend/", views.resend_verify_email, name="resend_verify_email"),
    path("logout/", views.logout_view, name="logout"),

    path("dashboard/", views.dashboard_view, name="dashboard"),

    path("orders/", views.orders_list_view, name="orders"),
    path("orders/<int:pk>/", views.order_detail_view, name="order_detail"),

    path("addresses/", views.address_list_create_view, name="addresses"),
    path("addresses/<int:pk>/default/", views.set_default_address_view, name="set_default_address"),
    path("addresses/<int:pk>/delete/", views.delete_address_view, name="delete_address"),

    path("password/change/", views.change_password_view, name="change_password"),

    path(
        "password/reset/",
        auth_views.PasswordResetView.as_view(
            form_class=StyledPasswordResetForm,
            template_name="password_reset_form.html",
            email_template_name="password_reset_email.txt",
            html_email_template_name="password_reset_email.html",
            subject_template_name="password_reset_subject.txt",
            success_url=reverse_lazy("password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "password/reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    
    path(
        "reset/<uidb64>/<token>/",
        PasswordResetConfirmCustomView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
]
