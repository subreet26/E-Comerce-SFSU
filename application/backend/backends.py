from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from .models import User


class BackendUserAuth(BaseBackend):
    """Authenticate against the backend User model using email and password hash."""

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
