
"""URLs de la app productos - W08 y exportación Excel."""

from django.urls import path
from . import views

app_name = 'productos'

urlpatterns = [
    # Ruta compatible con las pruebas W02.
    path('', views.ProductoListView.as_view(), name='inicio'),

    # Lectura (W07).
    path('', views.ProductoListView.as_view(), name='lista'),
    path('<int:producto_id>/', views.ProductoDetailView.as_view(), name='detalle'),

    # Escritura (W08).
    path('nuevo/', views.ProductoCreateView.as_view(), name='crear'),
    path('<int:producto_id>/editar/', views.ProductoUpdateView.as_view(), name='editar'),
    path('<int:producto_id>/eliminar/', views.ProductoDeleteView.as_view(), name='eliminar'),

    # Exportación Excel (W12).
    path('exportar-excel/', views.exportar_excel, name='exportar_excel'),
]
