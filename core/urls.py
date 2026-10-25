
# core/urls.py
"""Enrutador principal del ERP Django."""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Administración de Django
    path('admin/', admin.site.urls),

    # Inicio del ERP
    path('', views.bienvenida, name='inicio'),

    # Autenticación y cuentas con django-allauth
    path('accounts/', include('allauth.urls')),

    # Módulos del ERP
    path('clientes/', include('clientes.urls', namespace='clientes')),
    path('proveedores/', include('proveedores.urls', namespace='proveedores')),
    path('productos/', include('productos.urls', namespace='productos')),
    path('ventas/', include('ventas.urls', namespace='ventas')),
    path('reportes/', include('reportes.urls', namespace='reportes')),
]

# Archivos multimedia durante el desarrollo
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
