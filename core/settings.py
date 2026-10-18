
# core/settings.py
"""
Configuración principal del ERP Django.
Entorno de desarrollo y configuración base compartida con producción.
"""

import os
from pathlib import Path

import environ


# =========================================================
# RUTAS DEL PROYECTO
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# =========================================================
# VARIABLES DE ENTORNO
# =========================================================

env = environ.Env(
    DEBUG=(bool, True),
)

environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env(
    "SECRET_KEY",
    default="django-insecure-clave-solo-desarrollo-erp",
)

DEBUG = env("DEBUG")

ALLOWED_HOSTS = [
    host.strip()
    for host in env(
        "ALLOWED_HOSTS",
        default="localhost,127.0.0.1",
    ).split(",")
    if host.strip()
]


# =========================================================
# APLICACIONES INSTALADAS
# IMPORTANTE: JAZZMIN ANTES DE DJANGO ADMIN
# =========================================================


INSTALLED_APPS = [
    # Tema visual del administrador
    'jazzmin',

    # Aplicaciones propias de Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # API REST
    'rest_framework',

    # Aplicaciones del ERP
    'clientes',
    'proveedores',
    'productos',
    'ventas',
    'reportes',
    'configuracion',
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
# URLS Y APLICACIÓN WSGI
# =========================================================

ROOT_URLCONF = "core.urls"

WSGI_APPLICATION = "core.wsgi.application"

ASGI_APPLICATION = "core.asgi.application"


# =========================================================
# PLANTILLAS
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
# BASE DE DATOS DE DESARROLLO
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

STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
)


# =========================================================
# ARCHIVOS MULTIMEDIA
# =========================================================

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"


# =========================================================
# DJANGO REST FRAMEWORK
# =========================================================

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
}


# =========================================================
# MODELOS: CLAVE PRIMARIA PREDETERMINADA
# =========================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# =========================================================
# JAZZMIN — PERSONALIZACIÓN DEL ADMINISTRADOR
# ERP DJANGO · UTEC CELAYA
# =========================================================

JAZZMIN_SETTINGS = {
    # Identidad
    "site_title": "ERP Django",
    "site_header": "ERP UTEC Celaya",
    "site_brand": "📦 ERP Django",
    "welcome_sign": "Bienvenido al Sistema ERP · UTEC Celaya",
    "copyright": "MC. Román Fernando López González · UTEC Celaya",

    # Logo e icono
    "site_icon": None,
    "site_logo": None,

    # Búsqueda global
    "search_model": [
        "clientes.Cliente",
        "productos.Producto",
    ],

    # Menú superior
    "topmenu_links": [
        {
            "name": "Inicio ERP",
            "url": "/",
            "new_window": False,
        },
        {
            "name": "Productos",
            "url": "/productos/",
        },
        {
            "name": "Clientes",
            "url": "/clientes/",
        },
        {
            "name": "Ventas",
            "url": "/ventas/",
        },
    ],

    # Menú del usuario
    "usermenu_links": [
        {
            "name": "Ver ERP",
            "url": "/",
            "new_window": False,
        },
    ],

    # Orden de aplicaciones
    "order_with_respect_to": [
        "clientes",
        "proveedores",
        "productos",
        "ventas",
        "configuracion",
        "auth",
    ],

    # Iconos de los modelos
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",

        "clientes.Cliente": "fas fa-user-tie",
        "proveedores.Proveedor": "fas fa-truck",

        "productos.Categoria": "fas fa-tags",
        "productos.Producto": "fas fa-box",

        "ventas.Venta": "fas fa-file-invoice-dollar",
        "ventas.DetalleVenta": "fas fa-list",
        "ventas.Pedido": "fas fa-shopping-cart",

        "configuracion.ConfiguracionERP": "fas fa-cogs",
    },

    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-circle",

    # Apariencia y navegación
    "related_modal_active": True,
    "custom_css": "erp_custom.css",
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],

    # Formularios del administrador
    "changeform_format": "horizontal_tabs",
    "language_chooser": False,
}


# =========================================================
# JAZZMIN — ESTILO VISUAL AZULERP
# =========================================================

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,

    "brand_colour": "navbar-dark",
    "accent": "accent-navy",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,

    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-navy",

    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,

    "theme": "default",
    "dark_mode_theme": None,

    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}
