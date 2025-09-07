import os
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, True),
)
environ.Env.read_env(env_file=os.path.join(BASE_DIR, ".env"))

# Core
SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-secret-key")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = [h.strip() for h in env("DJANGO_ALLOWED_HOSTS", default="*").split(",")]

INSTALLED_APPS = [
    "django.contrib.admin",
    "bluewave_shop",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "accounts",
    "shop",
    "subscriptions",
    "metrics",
    "payments",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "bluewave_shop.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "bluewave_shop" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "bluewave_shop.context_processors.site_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "bluewave_shop.wsgi.application"

# Database
DB_ENGINE = env("DB_ENGINE", default="sqlite")
if DB_ENGINE == "mysql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": env("MYSQL_NAME"),
            "USER": env("MYSQL_USER"),
            "PASSWORD": env("MYSQL_PASSWORD"),
            "HOST": env("MYSQL_HOST", default="localhost"),
            "PORT": env("MYSQL_PORT", default="3306"),
            "OPTIONS": {"charset": "utf8mb4"},
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / env("DB_NAME", default="db.sqlite3"),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Europe/London"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "bluewave_shop" / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Security headers (tighten in production)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
X_FRAME_OPTIONS = "DENY"
SECURE_SSL_REDIRECT = False if DEBUG else True

# Stripe
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="")
STRIPE_PUBLISHABLE_KEY = env("STRIPE_PUBLISHABLE_KEY", default="")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default="")

# BlueWave API (correct endpoints + admin service account)
# Base defaults to the Flask dev server port
BLUEWAVE_API_BASE = env("BLUEWAVE_API_BASE", default="http://localhost:5000")

# Endpoints from the API repo
BLUEWAVE_API_JWT_ENDPOINT = env("BLUEWAVE_API_JWT_ENDPOINT", default="/auth/login")
BLUEWAVE_API_REGISTER_ENDPOINT = env("BLUEWAVE_API_REGISTER_ENDPOINT", default="/auth/register")
BLUEWAVE_API_METRICS_ENDPOINT = env("BLUEWAVE_API_METRICS_ENDPOINT", default="/observations")

# Admin service account (used to auto-register website users in the API)
BLUEWAVE_API_ADMIN_EMAIL = env("BLUEWAVE_API_ADMIN_EMAIL", default="")
BLUEWAVE_API_ADMIN_PASSWORD = env("BLUEWAVE_API_ADMIN_PASSWORD", default="")

# Auto-registration defaults (must match API schema)
BLUEWAVE_API_DEFAULT_ROLE = env("BLUEWAVE_API_DEFAULT_ROLE", default="researcher")
BLUEWAVE_API_DEFAULT_TIER = env("BLUEWAVE_API_DEFAULT_TIER", default="processed")
BLUEWAVE_API_DEFAULT_BUOY = env("BLUEWAVE_API_DEFAULT_BUOY", default="")  # only for device accounts

# Requests timeout to API
BLUEWAVE_API_TIMEOUT = env.int("BLUEWAVE_API_TIMEOUT", default=10)

# Site
SITE_NAME = env("SITE_NAME", default="BlueWave Solutions")
SITE_URL = env("SITE_URL", default="http://localhost:8000")

# Auth redirects
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/accounts/dashboard/"
LOGOUT_REDIRECT_URL = "/"
