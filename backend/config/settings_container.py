"""Container settings for the local Docker Compose deployment.

The bundled stack is intentionally HTTP-only and intended for local/educational
use. TLS is not terminated inside this Compose project. If the project is ever
published behind HTTPS, use a separate production settings module instead of
turning security flags on here.
"""

import os
from pathlib import Path

from .settings import *  # noqa: F401,F403


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _csv_env(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


DEBUG = _bool_env("DJANGO_DEBUG", False)
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", SECRET_KEY)  # noqa: F405
ALLOWED_HOSTS = _csv_env(
    "DJANGO_ALLOWED_HOSTS",
    "localhost,127.0.0.1,backend",
)

sqlite_path = Path(os.getenv("SQLITE_PATH", str(BASE_DIR / "db.sqlite3")))  # noqa: F405
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": sqlite_path,
    }
}

# Django owns only its own collected static files (admin/DRF). React is served
# by the separate nginx frontend container.
STATIC_URL = "/django-static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # noqa: F405
STATICFILES_DIRS = []
TEMPLATES[0]["DIRS"] = []  # noqa: F405

MIDDLEWARE = list(MIDDLEWARE)  # noqa: F405
security_middleware = "django.middleware.security.SecurityMiddleware"
whitenoise_middleware = "whitenoise.middleware.WhiteNoiseMiddleware"
if whitenoise_middleware not in MIDDLEWARE:
    try:
        security_index = MIDDLEWARE.index(security_middleware)
    except ValueError:
        security_index = -1
    MIDDLEWARE.insert(security_index + 1, whitenoise_middleware)

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ---------------------------------------------------------------------------
# Local HTTP / reverse proxy behaviour
# ---------------------------------------------------------------------------
# The Compose stack exposes plain HTTP on localhost. Be explicit so stale env
# variables or deployment defaults cannot turn local requests into HTTPS.
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_PROXY_SSL_HEADER = None
USE_X_FORWARDED_HOST = False

# Keep Django Admin protected by its normal CSRF middleware. Nginx preserves the
# original host+port, and these trusted origins cover the default local access
# points. APP_PORT is passed by docker-compose so custom local ports work too.
app_port = os.getenv("APP_PORT", "8080").strip() or "8080"
local_csrf_origins = [
    f"http://localhost:{app_port}",
    f"http://127.0.0.1:{app_port}",
]
extra_csrf_origins = _csv_env("CSRF_TRUSTED_ORIGINS")
CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(local_csrf_origins + extra_csrf_origins))

# Same-origin React -> Django requests do not need CORS. Keep an escape hatch
# for external development tools only.
CORS_ALLOWED_ORIGINS = _csv_env("CORS_ALLOWED_ORIGINS")

# The application's REST API is intentionally public in this educational
# project. Disabling SessionAuthentication is important: after logging into
# /admin/, the browser has a Django session cookie, and DRF would otherwise
# start requiring a CSRF token for React POST/DELETE requests. Django Admin is
# unaffected and continues to use normal authenticated sessions + CSRF.
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
}
