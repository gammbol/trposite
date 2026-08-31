"""Container/deployment overrides for the default Django settings.

The ordinary ``config.settings`` remains suitable for local development.
Docker Compose sets DJANGO_SETTINGS_MODULE=config.settings_container so the
container-specific filesystem, security and static-file settings stay isolated
from developer configuration.
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

# React is served by Nginx in another container. Django only owns its own
# collected static files (admin, DRF, etc.), avoiding a /static path collision
# with Create React App.
STATIC_URL = "/django-static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # noqa: F405
STATICFILES_DIRS = []
TEMPLATES[0]["DIRS"] = []  # noqa: F405

# Let Gunicorn/WhiteNoise serve Django static files if requested through Nginx.
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

# Requests from the bundled frontend are same-origin and therefore do not need
# CORS. Optional origins can still be supplied for external development tools.
CORS_ALLOWED_ORIGINS = _csv_env("CORS_ALLOWED_ORIGINS")
CSRF_TRUSTED_ORIGINS = _csv_env("CSRF_TRUSTED_ORIGINS")

# HTTPS-related flags are opt-in because the default Compose setup exposes plain
# HTTP on localhost. Enable them behind a TLS-terminating reverse proxy.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = _bool_env("DJANGO_SECURE_COOKIES", False)
CSRF_COOKIE_SECURE = _bool_env("DJANGO_SECURE_COOKIES", False)
