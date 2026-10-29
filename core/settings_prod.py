
"""
Configuración de producción para Render.
Hereda la configuración principal de core/settings.py.
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
# ARCHIVOS ESTÁTICOS Y ALMACENAMIENTO
# =========================================================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Configuración predeterminada:
# archivos multimedia en el sistema de archivos local.
# En producción, S3 se activa si existe AWS_STORAGE_BUCKET_NAME.
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
# ORÍGENES DE CONFIANZA PARA CSRF
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
# ARCHIVOS MULTIMEDIA — W11
# =========================================================

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# S3 es opcional. Si no hay nombre de bucket configurado,
# Django conserva el almacenamiento local predeterminado.

_bucket = os.environ.get("AWS_STORAGE_BUCKET_NAME", "").strip()

if _bucket:
    # Credenciales y configuración del bucket S3.
    AWS_ACCESS_KEY_ID = os.environ.get(
        "AWS_ACCESS_KEY_ID", ""
    )
    AWS_SECRET_ACCESS_KEY = os.environ.get(
        "AWS_SECRET_ACCESS_KEY", ""
    )
    AWS_STORAGE_BUCKET_NAME = _bucket

    AWS_S3_REGION_NAME = os.environ.get(
        "AWS_S3_REGION_NAME", "us-east-1"
    )

    AWS_DEFAULT_ACL = None
    AWS_S3_FILE_OVERWRITE = False
    AWS_QUERYSTRING_AUTH = False

    # Dominio CDN opcional.
    AWS_S3_CUSTOM_DOMAIN = os.environ.get(
        "AWS_S3_CUSTOM_DOMAIN", ""
    ).strip()

    # Django 4.2 utiliza STORAGES para definir el backend activo.
    STORAGES = {
        "default": {
            "BACKEND": (
                "storages.backends.s3boto3.S3Boto3Storage"
            ),
        },
        "staticfiles": {
            "BACKEND": (
                "whitenoise.storage.CompressedManifestStaticFilesStorage"
            ),
        },
    }

    # URL pública de las imágenes.
    if AWS_S3_CUSTOM_DOMAIN:
        MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"
    else:
        MEDIA_URL = (
            f"https://{_bucket}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/"
        )
