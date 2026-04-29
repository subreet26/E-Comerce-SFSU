# marketplace/backends.py
# Custom authentication backend for username OR email login
# Created on 04-29-2026

from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend


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
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            try:
                # If not found by username, try case-insensitive email lookup
                user = User.objects.get(email__iexact=username)
            except User.DoesNotExist:
                # User doesn't exist
                return None

        # Verify password
        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None

    def get_user(self, user_id):
        """Retrieve user by ID for session management."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
