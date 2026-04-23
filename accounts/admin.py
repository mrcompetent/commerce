from django.contrib import admin
from .models import Address, User, EmailOTP
# Register your models here.
admin.site.register(Address)
admin.site.register(User)
admin.site.register(EmailOTP)