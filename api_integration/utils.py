from django.conf import settings
from django.utils import timezone
import requests
from datetime import datetime, timedelta, timezone as dt_tz
from typing import Tuple, Optional

# PyJWT is optional (used only to parse exp); fall back gracefully if absent.
try:
    import jwt  # PyJWT
except Exception:
    jwt = None


def _decode_exp_noverify(token: str) -> Optional[datetime]:
    """
    Best-effort read of JWT 'exp' without verifying signature.
    If PyJWT is missing or 'exp' absent, return None.
    """
    if not jwt:
        return None
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        exp = payload.get("exp")
        if exp:
            return datetime.fromtimestamp(exp, tz=dt_tz.utc)
    except Exception:
        pass
    return None


def issue_jwt_for_user(user, *, email: Optional[str], password: str) -> Tuple[Optional[str], Optional[datetime], Optional[str]]:
    """
    Call BlueWave API /auth/login with {"email","password"}.
    Returns (token, expires_at, error).
    """
    jwt_path = getattr(settings, "BLUEWAVE_API_JWT_ENDPOINT", "/auth/login")
    url = settings.BLUEWAVE_API_BASE.rstrip('/') + jwt_path
    payload = {"email": email or (user.email or user.username), "password": password}

    try:
        resp = requests.post(url, json=payload, timeout=settings.BLUEWAVE_API_TIMEOUT)
        if resp.status_code >= 400:
            return None, None, f"API error {resp.status_code}: {resp.text}"
        data = resp.json()
        token = data.get("access_token") or data.get("token")
        if not token:
            return None, None, "API did not return access_token"
        expires_at = _decode_exp_noverify(token) or (timezone.now() + timedelta(hours=12))
        return token, expires_at, None
    except requests.RequestException as e:
        return None, None, str(e)


def fetch_metrics(start_iso: str, end_iso: str, token: Optional[str] = None):
    """
    Proxy call to the BlueWave metrics endpoint (/observations).
    If `token` is provided, send it in Authorization header.
    Returns (data, error).
    """
    metrics_path = getattr(settings, "BLUEWAVE_API_METRICS_ENDPOINT", "/observations")
    url = settings.BLUEWAVE_API_BASE.rstrip('/') + metrics_path
    params = {"start": start_iso, "end": end_iso}
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=settings.BLUEWAVE_API_TIMEOUT)
        if resp.status_code == 401:
            return None, "API error 401: Unauthorized (token missing/expired/invalid)"
        if resp.status_code >= 400:
            return None, f"API error {resp.status_code}: {resp.text}"
        return resp.json(), None
    except requests.RequestException as e:
        return None, str(e)


# ---------- Auto-register helpers ----------

def _admin_login_token() -> Tuple[Optional[str], Optional[str]]:
    admin_email = getattr(settings, "BLUEWAVE_API_ADMIN_EMAIL", None)
    admin_password = getattr(settings, "BLUEWAVE_API_ADMIN_PASSWORD", None)
    if not admin_email or not admin_password:
        return None, "Missing BLUEWAVE_API_ADMIN_EMAIL / BLUEWAVE_API_ADMIN_PASSWORD"

    jwt_path = getattr(settings, "BLUEWAVE_API_JWT_ENDPOINT", "/auth/login")
    url = settings.BLUEWAVE_API_BASE.rstrip('/') + jwt_path
    try:
        resp = requests.post(url, json={"email": admin_email, "password": admin_password},
                             timeout=settings.BLUEWAVE_API_TIMEOUT)
        if resp.status_code >= 400:
            return None, f"Admin login failed {resp.status_code}: {resp.text}"
        token = resp.json().get("access_token")
        if not token:
            return None, "Admin login returned no access_token"
        return token, None
    except requests.RequestException as e:
        return None, str(e)


def register_api_user(email: str, password: str, *, role: Optional[str] = None,
                      tier: Optional[str] = None, buoy_id: Optional[str] = None) -> Optional[str]:
    """
    Creates a user in the BlueWave API via /auth/register (admin-protected).
    Returns None on success, or an error string on failure.
    If the user already exists, returns None (treated as success).
    """
    admin_token, err = _admin_login_token()
    if err:
        return f"(skip) {err}"

    register_path = getattr(settings, "BLUEWAVE_API_REGISTER_ENDPOINT", "/auth/register")
    url = settings.BLUEWAVE_API_BASE.rstrip('/') + register_path

    payload = {"email": email, "password": password}
    if role: payload["role"] = role
    if tier: payload["tier"] = tier
    if buoy_id: payload["buoy_id"] = buoy_id

    headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=settings.BLUEWAVE_API_TIMEOUT)
        if resp.status_code in (200, 201):
            return None
        # treat "already exists" as success
        if resp.status_code in (400, 409) and "exists" in (resp.text or "").lower():
            return None
        return f"API register failed {resp.status_code}: {resp.text}"
    except requests.RequestException as e:
        return str(e)


def issue_jwt_with_autoreg(user, *, email: Optional[str], password: str) -> Tuple[Optional[str], Optional[datetime], Optional[str]]:
    """
    Try /auth/login; on 401 Invalid credentials, auto-register the user on the API then retry once.
    Returns (token, expires_at, error).
    """
    token, exp, err = issue_jwt_for_user(user, email=email, password=password)
    if not err:
        return token, exp, None

    # Only attempt auto-register on credential errors
    if "API error 401" in err or "Invalid credentials" in err:
        role = getattr(settings, "BLUEWAVE_API_DEFAULT_ROLE", "researcher")
        tier = getattr(settings, "BLUEWAVE_API_DEFAULT_TIER", "processed")
        buoy = getattr(settings, "BLUEWAVE_API_DEFAULT_BUOY", None)
        reg_err = register_api_user(email=email or (user.email or user.username),
                                    password=password, role=role, tier=tier, buoy_id=buoy)
        if reg_err and not reg_err.startswith("(skip)"):
            return None, None, f"Auto-register failed: {reg_err}"
        # Retry login once
        return issue_jwt_for_user(user, email=email, password=password)

    return None, None, err
