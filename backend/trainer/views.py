"""HTTP layer: parse requests, call services, return responses.

Keep logic out of here — put business rules in ``trainer/services`` and data
access in ``trainer/repositories``.
"""
import json

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from trainer.forms import CustomUserCreationForm
from trainer.services import AuthService, EtudeGenerationError, EtudeService


def index(request):
    """Serve the React app's page; React then decides what to show for the URL."""
    index_file = settings.FRONTEND_BUILD_DIR / "index.html"
    if not index_file.exists():
        return HttpResponse(
            "The frontend hasn't been built yet. Run `npm run build` in the frontend folder.",
            status=503,
            content_type="text/plain",
        )
    return HttpResponse(index_file.read_text())


def login_view(request):
    if request.method == "POST":
        user = AuthService().login(
            request,
            request.POST.get("username"),
            request.POST.get("password"),
        )
        if user is not None:
            return redirect("index")
        messages.error(request, "Invalid username or password")
    return render(request, "trainer/login.html")


def signup_view(request):
    if request.method == "POST":
        user, form = AuthService().signup(request, request.POST)
        if user is not None:
            return redirect("index")
    else:
        form = CustomUserCreationForm()
    return render(request, "trainer/signup.html", {"form": form})


@csrf_exempt
@require_http_methods(["POST"])
def generate_etude(request):
    """POST {"difficulty": "easy" | "medium" | "hard"} -> generated ABC notation."""
    try:
        body = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        body = None
    if not isinstance(body, dict):
        return JsonResponse({"success": False, "error": "Request body must be JSON"}, status=400)

    difficulty = body.get("difficulty")
    if difficulty is not None and difficulty not in EtudeService.DIFFICULTIES:
        return JsonResponse(
            {"success": False, "error": f"difficulty must be one of {', '.join(EtudeService.DIFFICULTIES)}"},
            status=400,
        )

    try:
        abc = EtudeService().generate(difficulty)
    except (EtudeGenerationError, OSError) as e:
        return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({
        "success": True,
        "abc_notation": abc,
        "message": "Etude generated successfully",
    })
