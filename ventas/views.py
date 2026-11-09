
# ventas/views.py
"""Vistas de la app ventas — W07, W08, W09 y tickets PDF."""

from decimal import Decimal

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
from django.http import HttpResponse
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
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
        return (
            Venta.objects
            .select_related('cliente')
            .prefetch_related('detalles__producto')
        )


@login_required
@permission_required('ventas.add_venta', raise_exception=True)
def crear_venta(request):
    """Crea una venta y redirige automáticamente a su ticket."""

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
                f'Venta #{venta.pk} registrada correctamente. '
                f'Total: ${venta.total:.2f}',
            )

            return redirect(
                'ventas:ticket',
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


def obtener_datos_ticket(venta):
    """Obtiene los detalles y calcula el importe de cada producto."""

    detalles = venta.detalles.select_related('producto').all()
    lineas = []

    for detalle in detalles:
        cantidad = detalle.cantidad
        precio = detalle.precio_unitario

        importe = Decimal(str(cantidad)) * Decimal(str(precio))

        lineas.append({
            'producto': detalle.producto,
            'cantidad': cantidad,
            'precio_unitario': precio,
            'importe': importe,
        })

    return lineas


@login_required
def venta_ticket(request, venta_id: int):
    """Muestra el ticket normal de una venta."""

    venta = get_object_or_404(
        Venta.objects
        .select_related('cliente')
        .prefetch_related('detalles__producto'),
        pk=venta_id,
    )

    context = {
        'venta': venta,
        'lineas': obtener_datos_ticket(venta),
        'es_pdf': False,
        'vista_previa': False,
    }

    return render(
        request,
        'ventas/ticket.html',
        context,
    )


@login_required
def venta_ticket_pdf(request, venta_id: int):
    """Muestra la vista previa del ticket en pantalla."""

    venta = get_object_or_404(
        Venta.objects
        .select_related('cliente')
        .prefetch_related('detalles__producto'),
        pk=venta_id,
    )

    context = {
        'venta': venta,
        'lineas': obtener_datos_ticket(venta),
        'es_pdf': False,
        'vista_previa': True,
    }

    return render(
        request,
        'ventas/ticket.html',
        context,
    )


@login_required
def venta_ticket_descargar_pdf(
    request,
    venta_id: int,
) -> HttpResponse:
    """Genera y descarga el ticket de venta en formato PDF."""

    import weasyprint

    venta = get_object_or_404(
        Venta.objects
        .select_related('cliente')
        .prefetch_related('detalles__producto'),
        pk=venta_id,
    )

    context = {
        'venta': venta,
        'lineas': obtener_datos_ticket(venta),
        'es_pdf': True,
        'vista_previa': False,
    }

    html_string = render_to_string(
        'ventas/ticket.html',
        context,
        request=request,
    )

    pdf_bytes = weasyprint.HTML(
        string=html_string,
        base_url=request.build_absolute_uri('/'),
    ).write_pdf()

    response = HttpResponse(
        pdf_bytes,
        content_type='application/pdf',
    )

    response['Content-Disposition'] = (
        f'attachment; filename="ticket_venta_{venta.pk:05d}.pdf"'
    )

    return response


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


@login_required
def venta_pdf(request, venta_id: int) -> HttpResponse:
    """Genera y descarga una factura PDF utilizando WeasyPrint."""

    import weasyprint

    from configuracion.models import ConfiguracionERP

    venta = get_object_or_404(
        Venta.objects
        .select_related('cliente')
        .prefetch_related('detalles__producto'),
        pk=venta_id,
    )

    config = ConfiguracionERP.get_instance()

    context = {
        'venta': venta,
        'config': config,
        'hoy': timezone.now(),
    }

    html_string = render_to_string(
        'ventas/factura_pdf.html',
        context,
        request=request,
    )

    pdf_bytes = weasyprint.HTML(
        string=html_string,
        base_url=request.build_absolute_uri('/'),
    ).write_pdf()

    response = HttpResponse(
        pdf_bytes,
        content_type='application/pdf',
    )

    response['Content-Disposition'] = (
        f'attachment; filename="factura_{venta.pk:05d}.pdf"'
    )

    return response
