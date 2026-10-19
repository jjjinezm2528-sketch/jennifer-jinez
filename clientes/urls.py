
# clientes/urls.py
"""URLs de la app clientes: Lista y Detalle."""

from django.urls import path
from . import views

app_name = 'clientes'

urlpatterns = [
    # Lista de clientes: conserva ambos nombres por compatibilidad.
    path(
        '',
        views.ClienteListView.as_view(),
        name='inicio',
    ),
    path(
        '',
        views.ClienteListView.as_view(),
        name='lista',
    ),

    # Detalle de un cliente.
    path(
        '<int:cliente_id>/',
        views.ClienteDetailView.as_view(),
        name='detalle',
    ),

    # Funciones pendientes de implementar.
    # path('nuevo/', views.ClienteCreateView.as_view(), name='crear'),
    # path('<int:cliente_id>/editar/', views.ClienteUpdateView.as_view(), name='editar'),
    # path('<int:cliente_id>/eliminar/', views.ClienteDeleteView.as_view(), name='eliminar'),
]
