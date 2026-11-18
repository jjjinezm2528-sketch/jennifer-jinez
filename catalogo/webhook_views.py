
# catalogo/webhook_views.py
"""Endpoint de webhook para recibir eventos de Stripe — W15/W16.

Verificación de seguridad:
    Stripe firma cada evento con STRIPE_WEBHOOK_SECRET.
    stripe.Webhook.construct_event() verifica la firma.

Eventos manejados:
    payment_intent.succeeded
        -> Pedido.estado = 'pagado'
        -> Descontar stock de productos
        -> Programar confirmación mediante Celery

    payment_intent.payment_failed
        -> Pedido.estado = 'cancelado'
"""

import logging

import stripe
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from productos.models import Producto
from ventas.models import Pedido

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def stripe_webhook(request) -> HttpResponse:
    """Recibe y procesa eventos de Stripe."""

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    # 1. Verificar firma de Stripe.
    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )

    except ValueError:
        logger.warning('Webhook: payload inválido recibido.')
        return HttpResponse('Payload inválido.', status=400)

    except stripe.error.SignatureVerificationError:
        logger.warning(
            'Webhook: firma inválida; posible intento de falsificación.'
        )
        return HttpResponse('Firma inválida.', status=400)

    # Convertir StripeObject a diccionario nativo.
    if hasattr(event, 'to_dict'):
        event = event.to_dict()

    # 2. Procesar evento.
    tipo = event['type']
    logger.info('Webhook recibido: %s', tipo)

    if tipo == 'payment_intent.succeeded':
        _manejar_pago_exitoso(event['data']['object'])

    elif tipo == 'payment_intent.payment_failed':
        _manejar_pago_fallido(event['data']['object'])

    else:
        logger.debug('Evento ignorado: %s', tipo)

    return HttpResponse(status=200)


# ---------------------------------------------------------------------
# HANDLERS INTERNOS
# ---------------------------------------------------------------------

def _manejar_pago_exitoso(payment_intent: dict) -> None:
    """Confirma el pago, descuenta inventario y programa la tarea Celery.

    La confirmación se programa solamente cuando el pedido cambia
    por primera vez de pendiente a pagado.
    """

    pedido_id = _extraer_pedido_id(payment_intent)

    if pedido_id is None:
        return

    try:
        with transaction.atomic():

            # Bloquea la fila durante la transacción para evitar
            # procesamientos simultáneos del mismo pedido.
            pedido = (
                Pedido.objects
                .select_for_update()
                .get(pk=pedido_id)
            )

            if pedido.estado != 'pagado':

                # Confirmar pedido.
                pedido.estado = 'pagado'
                pedido.save(update_fields=['estado'])

                logger.info(
                    'Pedido %s actualizado a pagado.',
                    pedido.numero_pedido,
                )

                # Descontar inventario una sola vez.
                _descontar_stock(pedido)

                # Guardar el ID antes de registrar el callback.
                pedido_pk = pedido.pk

                # Programar el correo únicamente después de que
                # la transacción de base de datos se haya confirmado.
                def programar_confirmacion():
                    from ventas.tasks import enviar_confirmacion_pedido

                    try:
                        enviar_confirmacion_pedido.delay(pedido_pk)

                        logger.info(
                            'Tarea de confirmación programada para '
                            'el pedido %s.',
                            pedido.numero_pedido,
                        )

                    except Exception:
                        logger.exception(
                            'No se pudo programar la confirmación '
                            'del pedido %s.',
                            pedido.numero_pedido,
                        )

                transaction.on_commit(programar_confirmacion)

            else:
                logger.info(
                    'Pedido %s ya estaba pagado. '
                    'Evento duplicado: no se repite el descuento '
                    'ni se programa otra confirmación.',
                    pedido.numero_pedido,
                )

    except Pedido.DoesNotExist:
        logger.error(
            'Webhook: Pedido %s no encontrado en la base de datos.',
            pedido_id,
        )


def _manejar_pago_fallido(payment_intent: dict) -> None:
    """Actualiza el pedido a cancelado cuando el pago falla."""

    pedido_id = _extraer_pedido_id(payment_intent)

    if pedido_id is None:
        return

    try:
        pedido = Pedido.objects.get(pk=pedido_id)

    except Pedido.DoesNotExist:
        logger.error(
            'Webhook: Pedido %s no encontrado en la base de datos.',
            pedido_id,
        )
        return

    if pedido.estado == 'pendiente':
        pedido.estado = 'cancelado'
        pedido.save(update_fields=['estado'])

        logger.info(
            'Pedido %s cancelado por pago fallido.',
            pedido.numero_pedido,
        )


def _extraer_pedido_id(payment_intent: dict) -> int | None:
    """Extrae el ID del pedido desde metadata de Stripe."""

    metadata = payment_intent.get('metadata', {})
    pedido_id = metadata.get('pedido_id')

    if not pedido_id:
        logger.warning(
            'Webhook: PaymentIntent sin pedido_id en metadata. '
            'ID: %s',
            payment_intent.get('id'),
        )
        return None

    try:
        return int(pedido_id)

    except (ValueError, TypeError):
        logger.error(
            'Webhook: pedido_id inválido: %r',
            pedido_id,
        )
        return None


def _descontar_stock(pedido: Pedido) -> None:
    """Descuenta el inventario usando expresiones F() de forma atómica."""

    items = pedido.items_snapshot or []

    for item in items:
        producto_id = item.get('producto_id')

        try:
            cantidad = int(item.get('cantidad', 0))
        except (ValueError, TypeError):
            logger.warning(
                'Cantidad inválida en el snapshot del pedido %s.',
                pedido.numero_pedido,
            )
            continue

        if not producto_id or cantidad <= 0:
            continue

        filas_actualizadas = (
            Producto.objects
            .filter(
                pk=producto_id,
                stock__gte=cantidad,
            )
            .update(
                stock=F('stock') - cantidad,
            )
        )

        if filas_actualizadas:
            logger.info(
                'Stock decrementado: Producto %s, '
                '%s unidades.',
                producto_id,
                cantidad,
            )

        else:
            logger.warning(
                'Producto %s: stock insuficiente para '
                'descontar %s unidades.',
                producto_id,
                cantidad,
            )
