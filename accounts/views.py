# accounts/views.py

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.conf import settings
from django.utils import timezone

from .forms import RegistrationForm, LoginForm, TOTPVerifyForm, TOTPSetupForm, APITokenRequestForm
from .models import UserProfile
from api_integration.utils import register_api_user  # (login token issuance is imported lazily below)
import pyotp, qrcode
from io import BytesIO
import base64

# Robust import for subscription model (supports either the simple or robust schema)
try:
    # simple schema (boolean `active`)
    from subscriptions.models import Subscription as SubModel
except Exception:
    # robust schema (status/current_period_end)
    from subscriptions.models import UserSubscription as SubModel

User = get_user_model()


def _has_active_subscription(user) -> bool:
    """
    Returns True if the user has an active subscription.
    Works for:
      - simple schema: SubModel has boolean 'active'
      - robust schema: SubModel has 'status', 'current_period_end', 'cancel_at_period_end'
    """
    field_names = {f.name for f in SubModel._meta.get_fields()}
    qs = SubModel.objects.filter(user=user)

    if "active" in field_names:
        # Simple model with boolean
        return qs.filter(active=True).exists()

    # Robust model: active if status in ('active','trialing') and period not expired
    allowed_status = ("active", "trialing")
    now = timezone.now()
    return qs.filter(status__in=allowed_status, current_period_end__gt=now).exists()


def get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def register_view(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]

            user = User.objects.create_user(username=username, email=email, password=password)
            get_or_create_profile(user)

            # Auto-register on BlueWave API (gracefully skipped if admin creds not set)
            default_role = getattr(settings, "BLUEWAVE_API_DEFAULT_ROLE", None)
            default_tier = getattr(settings, "BLUEWAVE_API_DEFAULT_TIER", None)
            default_buoy = getattr(settings, "BLUEWAVE_API_DEFAULT_BUOY", None)
            err = register_api_user(
                email=email,
                password=password,
                role=default_role,
                tier=default_tier,
                buoy_id=default_buoy,
            )
            if err and not err.startswith("(skip)"):
                messages.warning(request, f"Registered locally, but API user creation noted: {err}")

            messages.success(request, "Registration successful. Please log in.")
            return redirect("login")
    else:
        form = RegistrationForm()
    return render(request, "account/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data["username"], password=form.cleaned_data["password"])
            if user:
                profile = get_or_create_profile(user)
                request.session["pre_2fa_user_id"] = user.id
                if profile.totp_enabled:
                    return redirect("verify_totp")
                login(request, user)
                messages.success(request, "Welcome back!")
                return redirect("dashboard")
            else:
                messages.error(request, "Invalid credentials")
    else:
        form = LoginForm()
    return render(request, "account/login.html", {"form": form})


def verify_totp(request):
    user_id = request.session.get("pre_2fa_user_id")
    if not user_id:
        return redirect("login")
    user = User.objects.get(id=user_id)
    profile = get_or_create_profile(user)

    if request.method == "POST":
        form = TOTPVerifyForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]
            totp = pyotp.TOTP(profile.totp_secret)
            if totp.verify(code, valid_window=1):
                login(request, user)
                messages.success(request, "2FA success. You're in.")
                request.session.pop("pre_2fa_user_id", None)
                return redirect("dashboard")
            else:
                messages.error(request, "Invalid code. Try again.")
    else:
        form = TOTPVerifyForm()
    return render(request, "account/verify_totp.html", {"form": form})


@login_required
def setup_totp(request):
    profile = get_or_create_profile(request.user)
    if request.method == "POST":
        form = TOTPSetupForm(request.POST)
        if form.is_valid():
            if not profile.totp_secret:
                profile.totp_secret = pyotp.random_base32()
            profile.totp_enabled = True
            profile.save()
            messages.success(request, "TOTP enabled. Use your authenticator app at next login.")
            return redirect("dashboard")
    else:
        form = TOTPSetupForm()
        if not profile.totp_secret:
            profile.totp_secret = pyotp.random_base32()
            profile.save()

    issuer = settings.SITE_NAME
    totp = pyotp.TOTP(profile.totp_secret)
    uri = totp.provisioning_uri(name=request.user.email or request.user.username, issuer_name=issuer)
    img = qrcode.make(uri)
    buf = BytesIO()
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode("ascii")

    return render(
        request,
        "account/setup_totp.html",
        {"form": form, "qr_b64": qr_b64, "secret": profile.totp_secret},
    )


@login_required
def dashboard(request):
    profile = get_or_create_profile(request.user)
    return render(request, "account/dashboard.html", {"profile": profile})


@login_required
def api_access(request):
    profile = get_or_create_profile(request.user)
    # ✅ Authoritative check: only live subscriptions grant access
    has_researcher_access = _has_active_subscription(request.user)

    form = APITokenRequestForm(initial={"email": request.user.email})
    return render(
        request,
        "account/api_access.html",
        {
            "profile": profile,
            "form": form,
            "has_researcher_access": has_researcher_access,
            "BLUEWAVE_API_BASE": getattr(settings, "BLUEWAVE_API_BASE", "http://localhost:5000"),
            "BLUEWAVE_API_DOCS_URL": getattr(settings, "BLUEWAVE_API_DOCS_URL", None),
        },
    )


@login_required
def request_api_token(request):
    profile = get_or_create_profile(request.user)
    # ✅ Enforce live subscription for token requests
    has_researcher_access = _has_active_subscription(request.user)
    if not has_researcher_access:
        return HttpResponseForbidden("Subscription required to obtain API token.")

    form = APITokenRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data.get("email") or request.user.email
        password = form.cleaned_data["password"]

        # Try login; on 401, auto-register then retry
        from api_integration.utils import issue_jwt_with_autoreg
        token, expires_at, error = issue_jwt_with_autoreg(request.user, email=email, password=password)

        if error:
            messages.error(request, f"Failed to obtain token: {error}")
        else:
            profile.api_jwt = token or ""
            profile.api_jwt_expires_at = expires_at
            profile.save()
            messages.success(request, "API token issued successfully.")
    else:
        if request.method == "POST":
            messages.error(request, "Please enter your API password.")
    return redirect("api_access")


def logout_view(request):
    logout(request)
    messages.info(request, "Logged out.")
    return redirect("home")
