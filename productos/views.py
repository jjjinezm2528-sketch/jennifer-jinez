
"""Vistas de la app productos — W07, W08, W09 y exportación Excel."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

from .models import Producto
from .forms import ProductoForm


class ProductoListView(ListView):
    """Lista paginada de productos activos."""

    model = Producto
    template_name = 'productos/index.html'
    context_object_name = 'productos'
    paginate_by = 20

    def get_queryset(self):
        """Obtiene productos activos con sus relaciones precargadas."""
        return (
            Producto.objects
            .select_related('categoria', 'proveedor')
            .filter(activo=True)
            .order_by('nombre')
        )


class ProductoDetailView(DetailView):
    """Muestra los detalles de un producto."""

    model = Producto
    template_name = 'productos/detalle.html'
    context_object_name = 'producto'
    pk_url_kwarg = 'producto_id'

    def get_queryset(self):
        """Precarga las relaciones del producto."""
        return Producto.objects.select_related(
            'categoria',
            'proveedor',
        )


class ProductoCreateView(LoginRequiredMixin, CreateView):
    """Formulario para crear un producto."""

    model = Producto
    form_class = ProductoForm
    template_name = 'productos/crear.html'
    success_url = reverse_lazy('productos:lista')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Producto "{self.object.nombre}" creado exitosamente.',
        )
        return response


class ProductoUpdateView(LoginRequiredMixin, UpdateView):
    """Formulario para editar un producto existente."""

    model = Producto
    form_class = ProductoForm
    template_name = 'productos/editar.html'
    pk_url_kwarg = 'producto_id'
    success_url = reverse_lazy('productos:lista')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Producto "{self.object.nombre}" actualizado.',
        )
        return response


class ProductoDeleteView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    DeleteView,
):
    """Confirma y elimina un producto con permiso autorizado."""

    model = Producto
    template_name = 'productos/eliminar.html'
    pk_url_kwarg = 'producto_id'
    success_url = reverse_lazy('productos:lista')

    permission_required = 'productos.delete_producto'
    raise_exception = True

    def handle_no_permission(self):
        """Redirige usuarios anónimos y deniega usuarios sin permiso."""
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )

        return super().handle_no_permission()

    def form_valid(self, form):
        nombre = self.object.nombre
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Producto "{nombre}" eliminado.',
        )
        return response


@login_required
def exportar_excel(request):
    """Genera y descarga un Excel con el catálogo de productos."""

    productos = (
        Producto.objects
        .select_related('categoria', 'proveedor')
        .order_by('nombre')
    )

    libro = Workbook()
    hoja = libro.active
    hoja.title = 'Productos'

    encabezados = [
        'ID',
        'Nombre',
        'Precio',
        'Stock',
        'Categoría',
        'Proveedor',
        'Activo',
        'Fecha de registro',
    ]

    hoja.append(encabezados)

    # Estilo de encabezados.
    for celda in hoja[1]:
        celda.font = Font(bold=True, color='FFFFFF')
        celda.fill = PatternFill(
            fill_type='solid',
            fgColor='4B1F6F',
        )
        celda.alignment = Alignment(horizontal='center')

    # Datos de productos.
    for producto in productos:
        hoja.append([
            producto.pk,
            producto.nombre,
            float(producto.precio),
            producto.stock,
            producto.categoria.nombre,
            (
                producto.proveedor.nombre
                if producto.proveedor
                else 'Sin proveedor'
            ),
            'Sí' if producto.activo else 'No',
            (
                producto.creado.strftime('%d/%m/%Y %H:%M')
                if producto.creado
                else ''
            ),
        ])

    # Formato de columnas.
    anchos = {
        'A': 10,
        'B': 30,
        'C': 15,
        'D': 12,
        'E': 22,
        'F': 25,
        'G': 12,
        'H': 22,
    }

    for columna, ancho in anchos.items():
        hoja.column_dimensions[columna].width = ancho

    hoja.freeze_panes = 'A2'
    hoja.auto_filter.ref = hoja.dimensions

    respuesta = HttpResponse(
        content_type=(
            'application/vnd.openxmlformats-officedocument.'
            'spreadsheetml.sheet'
        )
    )

    respuesta['Content-Disposition'] = (
        'attachment; filename="productos_erp.xlsx"'
    )

    libro.save(respuesta)

    return respuesta
