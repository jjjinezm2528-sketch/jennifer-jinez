
# ventas/urls.py
from django.urls import path
from . import views

app_name = 'ventas'

urlpatterns = [
    # Rutas compatibles con las pruebas anteriores
    path('', views.VentaListView.as_view(), name='inicio'),
    path('', views.VentaListView.as_view(), name='lista'),

    # Crear y consultar ventas
    path('nueva/', views.crear_venta, name='crear'),

    # Ticket de venta
    path(
        '<int:venta_id>/ticket/',
        views.venta_ticket,
        name='ticket',
    ),
    path(
        '<int:venta_id>/ticket/pdf/',
        views.venta_ticket_pdf,
        name='ticket_pdf',
    ),

    # Detalle y eliminación
    path(
        '<int:venta_id>/',
        views.VentaDetailView.as_view(),
        name='detalle',
    ),
    path(
        '<int:venta_id>/eliminar/',
        views.VentaDeleteView.as_view(),
        name='eliminar',
    ),

    # Factura PDF anterior: se conserva
    path(
        '<int:venta_id>/pdf/',
        views.venta_pdf,
        name='pdf',
    ),
]
