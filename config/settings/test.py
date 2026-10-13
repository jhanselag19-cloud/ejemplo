"""
Settings para correr la suite de tests.
"""
from .base import *

DEBUG = False

# DB en memoria → tests mucho más rápidos
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Hasher rapidísimo → no perder tiempo hasheando passwords en tests
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Email que no envía nada
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"