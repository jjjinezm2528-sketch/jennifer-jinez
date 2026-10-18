
"""
Configuracion de produccion para Render.
Hereda la configuracion principal de core/settings.py.
"""

import os
import dj_database_url

from .settings import *

# =========================================================
# SEGURIDAD
# =========================================================

DEBUG = False

SECRET_KEY = os.environ.get("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        "Falta SECRET_KEY en las variables de entorno de Render."
    )

# =========================================================
# HOSTS PERMITIDOS
# =========================================================

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("ALLOWED_HOSTS", "").split(",")
    if host.strip()
]

RENDER_EXTERNAL_HOSTNAME = os.environ.get(
    "RENDER_EXTERNAL_HOSTNAME", ""
).strip()

if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

ALLOWED_HOSTS = list(dict.fromkeys(ALLOWED_HOSTS))

if not ALLOWED_HOSTS:
    raise RuntimeError(
        "Configura ALLOWED_HOSTS o verifica RENDER_EXTERNAL_HOSTNAME."
    )

# =========================================================
# BASE DE DATOS POSTGRESQL
# =========================================================

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "Falta DATABASE_URL. Configura PostgreSQL en Render."
    )

DATABASES = {
    "default": dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=True,
    )
}

# =========================================================
# ARCHIVOS ESTATICOS Y WHITENOISE
# =========================================================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}

# =========================================================
# SEGURIDAD HTTPS
# =========================================================

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# =========================================================
# ORIGENES DE CONFIANZA PARA CSRF
# =========================================================

CSRF_TRUSTED_ORIGINS = [
    f"https://{host}"
    for host in ALLOWED_HOSTS
    if host not in ("localhost", "127.0.0.1")
]

# =========================================================
# REGISTRO DE ERRORES
# =========================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
}

# =========================================================
# ARCHIVOS MULTIMEDIA
# =========================================================

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
