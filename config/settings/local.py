"""
Settings para desarrollo local.
"""
from .base import *

DEBUG = True
ALLOWED_HOSTS = ["*"]

# En local la DB vive en la raíz del proyecto
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Opcional: debug toolbar, django-extensions, etc.
INTERNAL_IPS = ["127.0.0.1"]