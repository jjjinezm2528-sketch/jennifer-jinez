
# ventas/urls.py
"""URLs de la app ventas: Lista y Detalle."""

from django.urls import path
from . import views

app_name = 'ventas'

urlpatterns = [
    # Lista de ventas: conserva ambos nombres.
    path(
        '',
        views.VentaListView.as_view(),
        name='inicio',
    ),
    path(
        '',
        views.VentaListView.as_view(),
        name='lista',
    ),

    # Detalle de una venta.
    path(
        '<int:venta_id>/',
        views.VentaDetailView.as_view(),
        name='detalle',
    ),

    # Funciones pendientes de implementar.
    # path('nuevo/', views.VentaCreateView.as_view(), name='crear'),
    # path('<int:venta_id>/editar/', views.VentaUpdateView.as_view(), name='editar'),
    # path('<int:venta_id>/eliminar/', views.VentaDeleteView.as_view(), name='eliminar'),
]
