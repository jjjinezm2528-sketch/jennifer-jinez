
# proveedores/urls.py
"""URLs de la app proveedores: Lista y Detalle."""

from django.urls import path
from . import views

app_name = 'proveedores'

urlpatterns = [
    # Lista de proveedores: conserva ambos nombres.
    path(
        '',
        views.ProveedorListView.as_view(),
        name='inicio',
    ),
    path(
        '',
        views.ProveedorListView.as_view(),
        name='lista',
    ),

    # Detalle de un proveedor.
    path(
        '<int:proveedor_id>/',
        views.ProveedorDetailView.as_view(),
        name='detalle',
    ),

    # Funciones pendientes de implementar.
    # path('nuevo/', views.ProveedorCreateView.as_view(), name='crear'),
    # path('<int:proveedor_id>/editar/', views.ProveedorUpdateView.as_view(), name='editar'),
    # path('<int:proveedor_id>/eliminar/', views.ProveedorDeleteView.as_view(), name='eliminar'),
]
