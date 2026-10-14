# clientes/urls.py
"""URLs de la app clientes — W02."""
from django.urls import path
from . import views

app_name = 'clientes'

urlpatterns = [
    path('', views.index, name='inicio'),
    # Espiral 2 W05:
    # path('lista/',          views.ClientesListView.as_view(),   name='lista'),
    # path('nuevo/',          views.ClientesCreateView.as_view(), name='crear'),
    # path('<int:pk>/',       views.ClientesDetailView.as_view(), name='detalle'),
    # path('<int:pk>/editar/',views.ClientesUpdateView.as_view(), name='editar'),
]
