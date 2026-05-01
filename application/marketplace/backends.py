# marketplace/backends.py
# Custom authentication backend for username OR email login
# Created on 04-29-2026

from django.contrib.auth.models import User as AuthUser
from django.contrib.auth.backends import ModelBackend, BaseBackend
from django.contrib.auth.hashers import check_password

from .models import User


class EmailOrUsernameBackend(ModelBackend):
    """
    Custom authentication backend that allows login via username OR email.
    Performs case-insensitive email lookup.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate via username (can be email or username) and password.
        
        Returns:
            User object if credentials are valid, None otherwise.
        """
        if not username or not password:
            return None

        try:
            # Try to find user by username first
            user = AuthUser.objects.get(username=username)
        except AuthUser.DoesNotExist:
            try:
                # If not found by username, try case-insensitive email lookup
                user = AuthUser.objects.get(email__iexact=username)
            except AuthUser.DoesNotExist:
                # User doesn't exist
                return None

        # Verify password
        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None

    def get_user(self, user_id):
        """Retrieve user by ID for session management."""
        try:
            return AuthUser.objects.get(pk=user_id)
        except AuthUser.DoesNotExist:
            return None


class BackendUserAuth(BaseBackend):
    """Authenticate against the marketplace User model using email and password hash."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        try:
            user = User.objects.get(sfsu_email=username)
        except User.DoesNotExist:
            return None

        if check_password(password, user.password_hash):
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
