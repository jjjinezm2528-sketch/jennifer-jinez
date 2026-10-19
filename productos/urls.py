
# productos/urls.py
"""URLs de la app productos: Lista y Detalle."""

from django.urls import path
from . import views

app_name = 'productos'

urlpatterns = [
    # Lista de productos: conserva ambos nombres.
    path(
        '',
        views.ProductoListView.as_view(),
        name='inicio',
    ),
    path(
        '',
        views.ProductoListView.as_view(),
        name='lista',
    ),

    # Detalle de un producto.
    path(
        '<int:producto_id>/',
        views.ProductoDetailView.as_view(),
        name='detalle',
    ),

    # Funciones pendientes de implementar.
    # path('nuevo/', views.ProductoCreateView.as_view(), name='crear'),
    # path('<int:producto_id>/editar/', views.ProductoUpdateView.as_view(), name='editar'),
    # path('<int:producto_id>/eliminar/', views.ProductoDeleteView.as_view(), name='eliminar'),
]
