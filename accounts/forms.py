from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import PasswordResetForm
from .models import Address
from django.contrib.auth.forms import SetPasswordForm

User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "input", "placeholder": "Email"})
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        widgets = {
            "username": forms.TextInput(attrs={"class": "input", "placeholder": "Username"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ add classes + ids for toggles
        self.fields["password1"].widget.attrs.update({
            "class": "input pw-input",
            "id": "register-password",
            "placeholder": "Password",
            "autocomplete": "new-password",
        })
        self.fields["password2"].widget.attrs.update({
            "class": "input pw-input",
            "id": "register-password2",
            "placeholder": "Confirm password",
            "autocomplete": "new-password",
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.is_active = False  # keep your OTP flow
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username or email",
        widget=forms.TextInput(attrs={"autofocus": True, "class": "input"}),
    )

    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "class": "input pw-input",
            "id": "login-password",
        })
    )


class OTPVerifyForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={
            "class": "input",
            "placeholder": "Enter 6-digit code"
        })
    )


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            "full_name","line1","line2","city","state","postal_code","country",
            "phone","address_type","is_default",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={"class":"input", "placeholder":"Full name"}),
            "line1": forms.TextInput(attrs={"class":"input", "placeholder":"Address line 1"}),
            "line2": forms.TextInput(attrs={"class":"input", "placeholder":"Address line 2 (optional)"}),
            "city": forms.TextInput(attrs={"class":"input", "placeholder":"City"}),
            "state": forms.TextInput(attrs={"class":"input", "placeholder":"State"}),
            "postal_code": forms.TextInput(attrs={"class":"input", "placeholder":"Postal code"}),
            "country": forms.TextInput(attrs={"class":"input", "placeholder":"Country"}),
            "phone": forms.TextInput(attrs={"class":"input", "placeholder":"Phone"}),

            # IMPORTANT: hide it (so it posts) and we’ll set a default
            "address_type": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # default address_type to shipping if not provided
        if not self.is_bound:
            self.fields["address_type"].initial = Address.AddressType.SHIPPING
        else:
            # if POST didn't include it for any reason, set it anyway
            if not self.data.get("address_type"):
                self.fields["address_type"].initial = Address.AddressType.SHIPPING



class PasswordChangeInlineForm(forms.Form):
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "input pw-input",
            "id": "current-password",
            "placeholder": "Current password",
            "autocomplete": "current-password",
        })
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "input pw-input",
            "id": "new-password",
            "placeholder": "New password",
            "autocomplete": "new-password",
        })
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "input pw-input",
            "id": "confirm-new-password",
            "placeholder": "Confirm new password",
            "autocomplete": "new-password",
        })
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        current = self.cleaned_data.get("current_password")
        if not self.user.check_password(current):
            raise ValidationError("Current password is incorrect.")
        return current

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("new_password1")
        p2 = cleaned.get("new_password2")

        if p1 and p2 and p1 != p2:
            self.add_error("new_password2", "Passwords do not match.")
            return cleaned

        if p1:
            password_validation.validate_password(p1, self.user)

        return cleaned
    

class StyledPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "input", "placeholder": "you@example.com"})
    )



class SetPasswordStyledForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["new_password1"].widget.attrs.update({
            "class": "input pw-input",
            "id": "reset-new-password",
            "placeholder": "New password",
            "autocomplete": "new-password",
        })
        self.fields["new_password2"].widget.attrs.update({
            "class": "input pw-input",
            "id": "reset-confirm-password",
            "placeholder": "Confirm new password",
            "autocomplete": "new-password",
        })