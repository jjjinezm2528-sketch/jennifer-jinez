
# ventas/views.py
"""Vistas de la app ventas — W07, W08 y W09."""

from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required,
    permission_required,
)
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import (
    DeleteView,
    DetailView,
    ListView,
)

from .forms import DetalleVentaForm, VentaForm
from .models import Venta


class VentaListView(ListView):
    """Lista paginada de ventas en orden cronológico inverso."""

    model = Venta
    template_name = 'ventas/index.html'
    context_object_name = 'ventas'
    paginate_by = 20

    def get_queryset(self):
        """Precarga el cliente para evitar consultas adicionales."""
        return (
            Venta.objects
            .select_related('cliente')
            .order_by('-fecha')
        )


class VentaDetailView(DetailView):
    """Detalle de una venta con sus líneas de producto."""

    model = Venta
    template_name = 'ventas/detalle.html'
    context_object_name = 'venta'
    pk_url_kwarg = 'venta_id'

    def get_queryset(self):
        """Precarga cliente y detalles de la venta."""
        return (
            Venta.objects
            .select_related('cliente')
            .prefetch_related('detalles__producto')
        )


@login_required
@permission_required('ventas.add_venta', raise_exception=True)
def crear_venta(request):
    """Crea un encabezado de venta con una línea de detalle.

    GET: muestra los dos formularios.
    POST: valida ambos y guarda si son correctos.
    """

    venta_form = VentaForm(request.POST or None)
    detalle_form = DetalleVentaForm(request.POST or None)

    if request.method == 'POST':
        if venta_form.is_valid() and detalle_form.is_valid():
            with transaction.atomic():
                venta = venta_form.save()
                detalle = detalle_form.save(commit=False)
                detalle.venta = venta
                detalle.save()

            messages.success(
                request,
                f'Venta #{venta.pk} registrada. '
                f'Total: ${venta.total:.2f}',
            )
            return redirect(
                'ventas:detalle',
                venta_id=venta.pk,
            )

    return render(
        request,
        'ventas/crear.html',
        {
            'venta_form': venta_form,
            'detalle_form': detalle_form,
        },
    )


class VentaDeleteView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    DeleteView,
):
    """Confirma y elimina una venta con permiso autorizado."""

    model = Venta
    template_name = 'ventas/eliminar.html'
    pk_url_kwarg = 'venta_id'
    success_url = reverse_lazy('ventas:lista')

    permission_required = 'ventas.delete_venta'
    raise_exception = True

    def form_valid(self, form):
        pk = self.object.pk
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Venta #{pk} eliminada.',
        )
        return response
