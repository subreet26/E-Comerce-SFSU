from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import UserProfile
import re


User = get_user_model()


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

        # case-insensitive uniqueness check (this project uses both fields)
        if User.objects.filter(email__iexact=email).exists() or User.objects.filter(sfsu_email__iexact=email).exists():
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

        special_chars = set('!@#$%^&*(),.?":{}|<>_-\\/[]')
        if not any(char in special_chars for char in password):
            raise ValidationError("Password must contain at least 1 special character.")

        return password

    # -------------------------
    # SAVE USER (IMPORTANT)
    # -------------------------
    def save(self, commit=True):
        user = super().save(commit=False)

        email = (self.cleaned_data.get("email") or "").strip().lower()
        user.email = email
        user.sfsu_email = email

        # Keep the legacy column populated; authentication uses `password`, but
        # other parts of the codebase read `password_hash`.
        user.password_hash = user.password

        if commit:
            user.save()
            UserProfile.objects.create(user=user)

        return user