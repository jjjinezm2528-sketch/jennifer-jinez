
# core/views.py
"""Vistas principales del proyecto ERP — W02.

Migración: HttpResponse → render() con templates y contexto.
"""
from django.shortcuts import render
from django.urls import reverse


from django.shortcuts import render
from django.urls import reverse


def bienvenida(request):
    modulos = [
        {"clave": "productos",   "nombre": "Productos",   "icono": "📦",
         "descripcion": "Inventario, precios y stock",    "url": reverse("productos:lista")},
        {"clave": "ventas",      "nombre": "Ventas",      "icono": "💰",
         "descripcion": "Pedidos, facturas y cobros",      "url": reverse("ventas:lista")},
        {"clave": "proveedores", "nombre": "Proveedores", "icono": "🏭",
         "descripcion": "Red de proveedores",              "url": reverse("proveedores:lista")},
        {"clave": "clientes",    "nombre": "Clientes",    "icono": "👥",
         "descripcion": "Cartera y su historial",          "url": reverse("clientes:lista")},
        {"clave": "reportes",    "nombre": "Reportes",    "icono": "📊",
         "descripcion": "Indicadores y gráficas",          "url": reverse("reportes:inicio")},
        {"clave": "tienda",      "nombre": "Tienda",      "icono": "🛒",
         "descripcion": "Catálogo y pedidos en línea",     "url": reverse("catalogo:catalogo")},
    ]
    return render(request, "home.html", {"modulos": modulos})