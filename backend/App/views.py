"""HTTP layer: parse requests, call services, return responses.

Keep logic out of here — put business rules in ``App/services`` and data
access in ``App/repositories``.
"""
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from App.forms import CustomUserCreationForm
from App.services import AuthService, EtudeGenerationError, EtudeService


def index(request):
    """Serve the React single-page app (built from /frontend)."""
    return render(request, "App/index.html")


def login_view(request):
    if request.method == "POST":
        user = AuthService().login(
            request,
            request.POST.get("username"),
            request.POST.get("password"),
        )
        if user is not None:
            return redirect(index)
        messages.error(request, "Invalid username or password")
    return render(request, "App/Login.html")


def signup_view(request):
    if request.method == "POST":
        user, form = AuthService().signup(request, request.POST)
        if user is not None:
            return redirect(index)
    else:
        form = CustomUserCreationForm()
    return render(request, "App/Sign_Up.html", {"form": form})


@csrf_exempt
@require_http_methods(["POST"])
def generate_etude(request):
    try:
        abc = EtudeService().generate()
    except (EtudeGenerationError, OSError) as e:
        return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({
        "success": True,
        "abc_notation": abc,
        "message": "Etude generated successfully",
    })
