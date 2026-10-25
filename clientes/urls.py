
# clientes/urls.py
from django.urls import path
from . import views

app_name = 'clientes'

urlpatterns = [
    # Ruta compatible con las pruebas W02
    path('', views.ClienteListView.as_view(), name='inicio'),

    # Rutas existentes
    path('', views.ClienteListView.as_view(), name='lista'),
    path('<int:cliente_id>/', views.ClienteDetailView.as_view(), name='detalle'),
    path('nuevo/', views.ClienteCreateView.as_view(), name='crear'),
    path('<int:cliente_id>/editar/', views.ClienteUpdateView.as_view(), name='editar'),
    path('<int:cliente_id>/eliminar/', views.ClienteDeleteView.as_view(), name='eliminar'),
]
