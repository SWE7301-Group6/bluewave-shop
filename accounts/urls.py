from django.urls import path
from .views import register_view, login_view, logout_view, dashboard, setup_totp, verify_totp, api_access, request_api_token

urlpatterns = [
    path("register/", register_view, name="register"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("dashboard/", dashboard, name="dashboard"),
    path("setup-totp/", setup_totp, name="setup_totp"),
    path("verify-totp/", verify_totp, name="verify_totp"),
    path("api-access/", api_access, name="api_access"),
    path("request-api-token/", request_api_token, name="request_api_token"),
]
