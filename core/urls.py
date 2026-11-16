# core/urls.py — Rutas principales del ERP y API REST

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from rest_framework.authtoken.views import obtain_auth_token

from . import views

# Importar y combinar todas las URLs de la API
from productos.api_urls import urlpatterns as productos_api
from clientes.api_urls import urlpatterns as clientes_api
from proveedores.api_urls import urlpatterns as proveedores_api
from ventas.api_urls import urlpatterns as ventas_api

api_urlpatterns = (
    productos_api
    + clientes_api
    + proveedores_api
    + ventas_api
)


def health(request):
    """Chequeo de salud sin acceso a base de datos (Docker / Render)."""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    # Salud del servicio
    path("health/", health, name="health"),

    # Administración
    path("admin/", admin.site.urls),

    # Página principal
    path("", views.bienvenida, name="inicio"),

    # Autenticación
    path("accounts/", include("allauth.urls")),

    # API REST (el token va ANTES del include genérico de la API)
    path("api/auth/token/", obtain_auth_token, name="api_token"),
    path("api/", include((api_urlpatterns, "api"))),

    # E-commerce público — W13
    path("catalogo/", include("catalogo.urls", namespace="catalogo")),

    # Aplicaciones del ERP (interfaz interna)
    path("clientes/", include("clientes.urls", namespace="clientes")),
    path("proveedores/", include("proveedores.urls", namespace="proveedores")),
    path("productos/", include("productos.urls", namespace="productos")),
    path("ventas/", include("ventas.urls", namespace="ventas")),
    path("reportes/", include("reportes.urls", namespace="reportes")),
]

# Archivos multimedia solo en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)