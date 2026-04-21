from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    # -------------------------
    # EMAIL VALIDATION
    # -------------------------
    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()

        # enforce SFSU domain
        if not email.endswith("@sfsu.edu"):
            raise ValidationError("Email must end with @sfsu.edu")

        # case-insensitive uniqueness check
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("This email is already in use.")

        return email

    # -------------------------
    # PASSWORD VALIDATION
    # -------------------------
    def clean_password1(self):
        password = self.cleaned_data.get("password1")

        if not password:
            return password

        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")

        if not re.search(r"[A-Z]", password):
            raise ValidationError("Password must contain at least 1 uppercase letter.")

        if not re.search(r"\d", password):
            raise ValidationError("Password must contain at least 1 number.")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-\\/\\[\\]]", password):
            raise ValidationError("Password must contain at least 1 special character.")

        return password

    # -------------------------
    # SAVE USER (IMPORTANT)
    # -------------------------
    def save(self, commit=True):
        user = super().save(commit=False)

        # store cleaned email
        user.email = self.cleaned_data["email"].strip().lower()

        if commit:
            user.save()

        return user