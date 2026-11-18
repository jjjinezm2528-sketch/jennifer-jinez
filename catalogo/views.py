# catalogo/views.py
"""Vistas del módulo de catálogo, carrito y checkout — W13/W14.

Módulo público (el catálogo no requiere autenticación).
El carrito se almacena en la sesión Django.

Estructura del carrito en sesión:
    request.session['carrito'] = {
        '1': {
            'nombre':   'Laptop HP',
            'precio':   '10000.00',   # str: Decimal no es JSON serializable
            'cantidad': 2,
            'imagen':   'productos/laptop.jpg'  # o None
        },
    }
"""

import logging
from decimal import ROUND_HALF_UP, Decimal

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import ListView

from productos.models import Producto
from ventas.models import Pedido

from .checkout_utils import (
    armar_items,
    calcular_totales,
    generar_numero_pedido,
    obtener_o_crear_cliente,
)
from .filters import ProductoFilter

logger = logging.getLogger(__name__)

# Clave secreta de Stripe (definida por variable de entorno en settings)
stripe.api_key = settings.STRIPE_SECRET_KEY

# Límite de unidades por producto en el carrito
MAX_CANTIDAD_POR_LINEA = 99


# ── CATÁLOGO ───────────────────────────────────────────────────────────────

class CatalogoView(ListView):
    """Catálogo público de productos con filtros.

    No requiere autenticación — accesible para cualquier visitante.
    """

    model = Producto
    template_name = 'catalogo/catalogo.html'
    context_object_name = 'productos'
    paginate_by = 12  # 3 filas de 4 tarjetas

    def get_queryset(self):
        """Filtra productos activos aplicando los filtros del request."""
        qs = (
            Producto.objects
            .select_related('categoria', 'proveedor')
            .filter(activo=True)
            .order_by('nombre')
        )
        self.filtro = ProductoFilter(self.request.GET, queryset=qs)
        return self.filtro.qs

    def get_context_data(self, **kwargs):
        """Agrega el objeto filtro al contexto para renderizar el formulario."""
        ctx = super().get_context_data(**kwargs)
        ctx['filtro'] = self.filtro
        ctx['categorias'] = self.filtro.form.fields['categoria'].queryset
        return ctx


# ── UTILIDADES DEL CARRITO ─────────────────────────────────────────────────

def _obtener_carrito(request) -> dict:
    """Obtiene el carrito de la sesión o crea uno vacío."""
    return request.session.get('carrito', {})


def _guardar_carrito(request, carrito: dict) -> None:
    """Guarda el carrito en la sesión y lo marca como modificado."""
    request.session['carrito'] = carrito
    request.session.modified = True


def _leer_cantidad(valor, default: int = 1) -> int:
    """Convierte a entero acotado entre 0 y MAX_CANTIDAD_POR_LINEA."""
    try:
        cantidad = int(valor)
    except (TypeError, ValueError):
        return default
    return max(0, min(cantidad, MAX_CANTIDAD_POR_LINEA))


def _url_segura(request, url):
    """Devuelve la URL solo si apunta a este mismo sitio (evita open redirect)."""
    if url and url_has_allowed_host_and_scheme(
        url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return url
    return None


def _sincronizar_carrito(request, carrito: dict) -> dict:
    """Actualiza precios y nombres desde la BD y quita productos inactivos."""
    if not carrito:
        return carrito

    try:
        ids = [int(clave) for clave in carrito]
    except ValueError:
        _guardar_carrito(request, {})
        return {}

    activos = {
        p.pk: p
        for p in Producto.objects.filter(pk__in=ids, activo=True)
    }

    hubo_cambios = False
    for clave in list(carrito):
        producto = activos.get(int(clave))
        if producto is None:
            carrito.pop(clave)
            hubo_cambios = True
            continue
        if carrito[clave].get('precio') != str(producto.precio):
            carrito[clave]['precio'] = str(producto.precio)
            hubo_cambios = True
        carrito[clave]['nombre'] = producto.nombre

    if hubo_cambios:
        _guardar_carrito(request, carrito)
        messages.warning(
            request,
            'Actualizamos tu carrito: algunos precios cambiaron o '
            'ciertos productos ya no están disponibles.'
        )
    return carrito


def _pedido_pendiente(request, cliente):
    """Reutiliza el pedido pendiente de esta sesión, si existe."""
    pk = request.session.get('pedido_pendiente_id')
    if not pk:
        return None
    return Pedido.objects.filter(
        pk=pk, cliente=cliente, estado='pendiente'
    ).first()


# ── CARRITO ────────────────────────────────────────────────────────────────

def ver_carrito(request):
    """Muestra el carrito con subtotales y total.

    Convierte los precios de str a Decimal para el cálculo.
    """
    carrito = _sincronizar_carrito(request, _obtener_carrito(request))

    items = []
    total = Decimal('0.00')

    for prod_id, datos in carrito.items():
        precio = Decimal(datos['precio'])
        cantidad = int(datos['cantidad'])
        subtotal = precio * cantidad
        total += subtotal
        items.append({
            'prod_id':  prod_id,
            'nombre':   datos['nombre'],
            'precio':   precio,
            'cantidad': cantidad,
            'subtotal': subtotal,
            'imagen':   datos.get('imagen'),
        })

    return render(request, 'catalogo/carrito.html', {
        'items': items,
        'total': total,
    })


def agregar_al_carrito(request, producto_id: int):
    """Agrega un producto al carrito. Solo POST.

    La cantidad se valida (1 a MAX_CANTIDAD_POR_LINEA) y la URL de
    retorno solo se acepta si pertenece a este mismo sitio.
    """
    if request.method != 'POST':
        return redirect('catalogo:catalogo')

    producto = get_object_or_404(Producto, pk=producto_id, activo=True)

    cantidad = _leer_cantidad(request.POST.get('cantidad', 1))
    if cantidad < 1:
        messages.error(request, 'La cantidad debe ser al menos 1.')
        return redirect('catalogo:catalogo')

    carrito = _obtener_carrito(request)
    clave = str(producto_id)

    if clave in carrito:
        nueva = carrito[clave]['cantidad'] + cantidad
        carrito[clave]['cantidad'] = min(nueva, MAX_CANTIDAD_POR_LINEA)
    else:
        carrito[clave] = {
            'nombre':   producto.nombre,
            'precio':   str(producto.precio),
            'cantidad': cantidad,
            'imagen':   producto.imagen.name if producto.imagen else None,
        }

    _guardar_carrito(request, carrito)
    messages.success(request, f'"{producto.nombre}" agregado al carrito.')

    destino = _url_segura(
        request,
        request.POST.get('next') or request.META.get('HTTP_REFERER'),
    )
    return redirect(destino or 'catalogo:catalogo')


def remover_del_carrito(request, producto_id: int):
    """Elimina un producto del carrito. Solo POST."""
    if request.method != 'POST':
        return redirect('catalogo:carrito')

    carrito = _obtener_carrito(request)
    clave = str(producto_id)

    nombre = carrito.get(clave, {}).get('nombre', 'Producto')
    carrito.pop(clave, None)
    _guardar_carrito(request, carrito)

    messages.warning(request, f'"{nombre}" eliminado del carrito.')
    return redirect('catalogo:carrito')


def actualizar_cantidad(request, producto_id: int):
    """Actualiza la cantidad de un producto. Solo POST.

    Si la cantidad llega a 0, elimina el item.
    """
    if request.method != 'POST':
        return redirect('catalogo:carrito')

    carrito = _obtener_carrito(request)
    clave = str(producto_id)
    cantidad = _leer_cantidad(request.POST.get('cantidad', 1))

    if clave in carrito:
        if cantidad > 0:
            carrito[clave]['cantidad'] = cantidad
        else:
            carrito.pop(clave)

    _guardar_carrito(request, carrito)
    return redirect('catalogo:carrito')


def vaciar_carrito(request):
    """Elimina todos los productos del carrito. Solo POST."""
    if request.method == 'POST':
        _guardar_carrito(request, {})
        messages.info(request, 'Carrito vaciado.')
    return redirect('catalogo:carrito')


# ── CHECKOUT (Stripe) ──────────────────────────────────────────────────────

@login_required
def checkout(request):
    """Resumen del carrito y creación del PaymentIntent de Stripe.

    GET:  muestra el resumen con IVA calculado (sin PaymentIntent).
    POST: sincroniza precios con la BD, crea o reutiliza el Pedido
          pendiente y crea el PaymentIntent. Devuelve client_secret
          al template para que Stripe.js confirme el pago.

    Redirige a /catalogo/ si el carrito está vacío.
    """
    carrito = _sincronizar_carrito(request, _obtener_carrito(request))
    if not carrito:
        messages.warning(request, 'Tu carrito está vacío.')
        return redirect('catalogo:catalogo')

    totales = calcular_totales(carrito)
    items = armar_items(carrito)
    publishable_key = settings.STRIPE_PUBLISHABLE_KEY

    if request.method == 'POST':
        try:
            cliente = obtener_o_crear_cliente(request.user)

            snapshot = [
                {
                    'producto_id': int(prod_id),
                    'nombre':      datos['nombre'],
                    'cantidad':    int(datos['cantidad']),
                    'precio':      datos['precio'],  # ya es str
                }
                for prod_id, datos in carrito.items()
            ]

            total = Decimal(str(totales['total']))

            with transaction.atomic():
                pedido = _pedido_pendiente(request, cliente)
                if pedido is None:
                    pedido = Pedido.objects.create(
                        numero_pedido=generar_numero_pedido(),
                        cliente=cliente,
                        estado='pendiente',
                        total_pagado=total,
                        items_snapshot=snapshot,
                    )
                    request.session['pedido_pendiente_id'] = pedido.pk
                else:
                    pedido.total_pagado = total
                    pedido.items_snapshot = snapshot
                    pedido.save(
                        update_fields=['total_pagado', 'items_snapshot']
                    )

            # Stripe requiere el monto como entero en centavos
            monto_centavos = int(
                (total * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            )

            intent = stripe.PaymentIntent.create(
                amount=monto_centavos,
                currency='mxn',
                metadata={
                    'pedido_id':  pedido.pk,
                    'pedido_num': pedido.numero_pedido,
                    'cliente':    cliente.nombre,
                },
                # Incluye el monto: Stripe rechaza reutilizar una clave
                # con parámetros distintos
                idempotency_key=f'pedido-{pedido.pk}-{monto_centavos}',
            )

            return render(request, 'catalogo/checkout.html', {
                'carrito':         carrito,
                'items':           items,
                'totales':         totales,
                'pedido':          pedido,
                'client_secret':   intent.client_secret,
                'publishable_key': publishable_key,
            })

        except stripe.StripeError as exc:
            logger.exception('Error de Stripe en checkout')
            detalle = getattr(exc, 'user_message', None) or 'Intenta de nuevo.'
            messages.error(
                request,
                f'No pudimos conectar con el procesador de pagos. {detalle}'
            )
            return redirect('catalogo:pago_error')

        except Exception:
            logger.exception('Error inesperado en checkout')
            messages.error(
                request,
                'Ocurrió un error inesperado en el proceso de pago. '
                'Intenta de nuevo más tarde.'
            )
            return redirect('catalogo:pago_error')

    # GET — solo mostrar resumen (sin PaymentIntent)
    return render(request, 'catalogo/checkout.html', {
        'carrito':         carrito,
        'items':           items,
        'totales':         totales,
        'client_secret':   None,
        'publishable_key': publishable_key,
    })


def pago_exitoso(request, pedido_id: int):
    """Muestra la confirmación únicamente cuando el pago está registrado."""

    pedido = get_object_or_404(Pedido, pk=pedido_id)

    if pedido.estado != 'pagado':
        logger.info(
            'El pedido %s todavía no está confirmado. Estado: %s',
            pedido.numero_pedido,
            pedido.estado,
        )

        return render(
            request,
            'catalogo/pago_pendiente.html',
            {'pedido': pedido},
            status=200,
        )

    # Vaciar el carrito solamente después de confirmar el pago.
    _guardar_carrito(request, {})
    request.session.pop('pedido_pendiente_id', None)

    messages.success(
        request,
        f'¡Pago exitoso! Tu pedido {pedido.numero_pedido} '
        f'está confirmado. Total: ${pedido.total_pagado}'
    )

    return render(request, 'catalogo/pago_exitoso.html', {
        'pedido': pedido,
    })

def pago_error(request):
    """Vista de error de pago — muestra mensaje y permite reintentar."""
    return render(request, 'catalogo/pago_error.html')