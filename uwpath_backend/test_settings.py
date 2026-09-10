"""Settings for local and CI tests that do not require the legacy Oracle database."""

from .local_settings import *  # noqa: F403

SECRET_KEY = "uwpath-test-key"
ALLOWED_HOSTS = ["testserver"]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
