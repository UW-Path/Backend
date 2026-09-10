"""Local settings for exploring file-backed catalogs without Oracle."""

from .local_settings import *  # noqa: F403

SECRET_KEY = "uwpath-local-catalog-playground"
ALLOWED_HOSTS = ["0.0.0.0", "127.0.0.1", "localhost"]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
