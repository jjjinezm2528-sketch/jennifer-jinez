
# ventas/urls.py
from django.urls import path
from . import views

app_name = 'ventas'

urlpatterns = [
    # Ruta compatible con las pruebas W02
    path('', views.VentaListView.as_view(), name='inicio'),

    # Rutas existentes
    path('', views.VentaListView.as_view(), name='lista'),
    path('<int:venta_id>/', views.VentaDetailView.as_view(), name='detalle'),
    path('nueva/', views.crear_venta, name='crear'),
    path('<int:venta_id>/eliminar/', views.VentaDeleteView.as_view(), name='eliminar'),
]
