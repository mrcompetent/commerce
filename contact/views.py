# contact/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.shortcuts import render, redirect
from django.contrib import messages

from .forms import ContactForm


def contact_view(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save()

            # 🔹 EMAIL CONTEXT
            ctx = {
                "name": contact.name,
                "email": contact.email,
                "subject": contact.subject,
                "message": contact.message,
            }

            # 🔹 RENDER EMAIL TEMPLATES
            subject = f"[Contact] {contact.subject}"
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [settings.DEFAULT_FROM_EMAIL]  # support team email

            text_body = render_to_string("contact_email.txt", ctx)
            html_body = render_to_string("contact_email.html", ctx)

            # 🔹 SEND EMAIL
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_body,
                from_email=from_email,
                to=to_email,
                reply_to=[contact.email],  # allows reply directly to user
            )
            email.attach_alternative(html_body, "text/html")
            email.send()

            messages.success(
                request,
                "Thank you for contacting us. We’ll get back to you shortly."
            )
            return redirect("contact")
    else:
        form = ContactForm()

    return render(request, "contact.html", {
        "form": form
    })