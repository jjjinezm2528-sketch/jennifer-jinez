
"""
Configuración principal del proyecto ERP Django.
"""

from pathlib import Path
import environ

# =========================================================
# RUTAS DEL PROYECTO
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# =========================================================
# VARIABLES DE ENTORNO
# =========================================================

env = environ.Env()
env.read_env(BASE_DIR / ".env")

# =========================================================
# SEGURIDAD Y DEPURACIÓN
# =========================================================

SECRET_KEY = env(
    "SECRET_KEY",
    default="clave-temporal-solo-para-desarrollo"
).strip()

DEBUG = (
    env("DEBUG", default="False").strip().lower()
    in ("1", "true", "yes", "on")
)

# Quita espacios sobrantes de cada dirección.
_hosts = env(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1"
)

ALLOWED_HOSTS = [
    host.strip()
    for host in _hosts.split(",")
    if host.strip()
]

# =========================================================
# APLICACIONES
# =========================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",
    "whitenoise.runserver_nostatic",

    # Aplicaciones del ERP
    "clientes",
    "proveedores",
    "productos",
    "ventas",
    "reportes",
]

# =========================================================
# MIDDLEWARE
# =========================================================

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

# =========================================================
# URLS Y SERVIDOR
# =========================================================

ROOT_URLCONF = "core.urls"

WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"

# =========================================================
# PLANTILLAS HTML
# =========================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# =========================================================
# BASE DE DATOS SQLITE
# =========================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# =========================================================
# VALIDACIÓN DE CONTRASEÑAS
# =========================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]

# =========================================================
# IDIOMA Y ZONA HORARIA
# =========================================================

LANGUAGE_CODE = "es-mx"

TIME_ZONE = "America/Mexico_City"

USE_I18N = True

USE_TZ = True


# =========================================================
# ARCHIVOS ESTÁTICOS
# =========================================================
# settings.py — sección de estáticos (verificar, no duplicar)
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'   # destino de collectstatic

# STATICFILES_DIRS ≠ STATIC_ROOT (error frecuente)
STATICFILES_DIRS = [BASE_DIR / 'static']  # fuentes adicionales

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'




# =========================================================
# ARCHIVOS MULTIMEDIA
# =========================================================

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"

# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =========================================================
# DJANGO REST FRAMEWORK
# =========================================================

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
}
