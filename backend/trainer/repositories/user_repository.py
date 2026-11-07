from django.contrib.auth.models import User


class UserRepository:
    """Access to Django's built-in auth_user table."""

    def get_by_username(self, username):
        return User.objects.filter(username=username).first()

    def username_exists(self, username):
        return User.objects.filter(username=username).exists()
