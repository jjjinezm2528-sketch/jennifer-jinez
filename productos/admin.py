
# productos/admin.py
"""Configuración del panel admin para la app productos."""

from django.contrib import admin
from django.utils.html import format_html

from .models import Categoria, Producto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    """Admin de categorías."""

    list_display = ['pk', 'nombre', 'descripcion']
    search_fields = ['nombre']


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    """Admin de productos: lista con categoría, proveedor,
    stock e imagen."""

    list_display = [
        'pk',
        'mostrar_imagen',
        'nombre',
        'precio',
        'stock',
        'categoria',
        'proveedor',
        'activo',
        'creado',
    ]

    search_fields = [
        'nombre',
        'categoria__nombre',
        'proveedor__nombre',
    ]

    list_filter = ['activo', 'categoria']

    list_editable = ['precio', 'stock', 'activo']

    readonly_fields = ['creado', 'vista_previa_imagen']

    fields = [
        'nombre',
        'precio',
        'stock',
        'categoria',
        'proveedor',
        'activo',
        'imagen',
        'vista_previa_imagen',
        'creado',
    ]

    autocomplete_fields = ['proveedor']
    date_hierarchy = 'creado'
    ordering = ['nombre']

    @admin.display(description='Imagen')
    def mostrar_imagen(self, obj):
        """Muestra una miniatura en la lista de productos."""
        if obj.imagen:
            return format_html(
                '<img src="{}" width="50" height="50" '
                'style="object-fit:contain; border-radius:6px;" />',
                obj.imagen.url,
            )

        return 'Sin imagen'

    @admin.display(description='Vista previa de imagen')
    def vista_previa_imagen(self, obj):
        """Muestra la imagen actual en el formulario de administración."""
        if obj and obj.imagen:
            return format_html(
                '<img src="{}" width="180" '
                'style="max-height:180px; object-fit:contain; '
                'border-radius:8px;" />',
                obj.imagen.url,
            )

        return 'Sin imagen cargada'
