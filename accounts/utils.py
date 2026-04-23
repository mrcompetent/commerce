# accounts/utils.py
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone


def send_otp_email(to_email: str, code: str, *, username: str = "", minutes_valid: int = 10):
    subject = "Your verification code"
    from_email = settings.DEFAULT_FROM_EMAIL

    ctx = {
        "code": code,
        "username": username,
        "minutes_valid": minutes_valid,
        "year": timezone.now().year,
    }

    text_body = render_to_string("otp_email.txt", ctx)
    html_body = render_to_string("otp_email.html", ctx)

    msg = EmailMultiAlternatives(subject, text_body, from_email, [to_email])
    msg.attach_alternative(html_body, "text/html")
    msg.send()
