from django.contrib.auth import authenticate, login

from App.forms import CustomUserCreationForm


class AuthService:
    """Log users in and register new accounts."""

    def login(self, request, username, password):
        """Authenticate and start a session. Returns the user or None."""
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
        return user

    def signup(self, request, data):
        """Validate and create a user, then log them in.

        Returns ``(user, form)``; ``user`` is None when the form is invalid.
        """
        form = CustomUserCreationForm(data)
        if not form.is_valid():
            return None, form
        user = form.save()
        login(request, user)
        return user, form
