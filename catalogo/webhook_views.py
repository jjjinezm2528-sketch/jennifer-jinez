
# catalogo/webhook_views.py
"""Endpoint de webhook para recibir eventos de Stripe.

W15/W16/W17.

Eventos manejados:
    payment_intent.succeeded:
        - Confirma el pedido.
        - Descuenta el inventario una sola vez.
        - Envía directamente el correo de confirmación.

    payment_intent.payment_failed:
        - Cancela el pedido pendiente.

El envío directo utiliza Django + SendGrid y no necesita
un Celery Worker.
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

    # 1. Verificar la firma del evento.
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

    # 2. Convertir StripeObject a diccionario nativo.
    if hasattr(event, 'to_dict'):
        event = event.to_dict()

    # 3. Procesar el evento.
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
    """
    Confirma el pago, descuenta inventario y envía la confirmación.

    La confirmación se intenta únicamente cuando el pedido cambia
    por primera vez de pendiente a pagado.
    """

    pedido_id = _extraer_pedido_id(payment_intent)

    if pedido_id is None:
        return

    try:
        with transaction.atomic():

            # Bloquear la fila para evitar procesamientos simultáneos.
            pedido = (
                Pedido.objects
                .select_for_update()
                .get(pk=pedido_id)
            )

            if pedido.estado != 'pagado':

                # Confirmar el pedido.
                pedido.estado = 'pagado'
                pedido.save(update_fields=['estado'])

                logger.info(
                    'Pedido %s actualizado a pagado.',
                    pedido.numero_pedido
                )

                # Descontar inventario una sola vez.
                _descontar_stock(pedido)

                pedido_pk = pedido.pk
                numero_pedido = pedido.numero_pedido

                # Ejecutar el envío después de confirmar la transacción.
                def programar_confirmacion():
                    from ventas.tasks import (
                        enviar_confirmacion_pedido_directo
                    )

                    try:
                        resultado = (
                            enviar_confirmacion_pedido_directo(pedido_pk)
                        )

                        logger.info(
                            'Resultado del correo para pedido %s: %s',
                            numero_pedido,
                            resultado,
                        )

                    except Exception:
                        logger.exception(
                            'No se pudo enviar la confirmación '
                            'del pedido %s.',
                            numero_pedido,
                        )

                transaction.on_commit(programar_confirmacion)

            else:
                logger.info(
                    'Pedido %s ya estaba pagado. '
                    'Evento duplicado: no se repite el descuento '
                    'ni se programa otra confirmación.',
                    pedido.numero_pedido
                )

    except Pedido.DoesNotExist:
        logger.error(
            'Webhook: Pedido %s no encontrado en la base de datos.',
            pedido_id
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
            pedido_id
        )
        return

    if pedido.estado == 'pendiente':
        pedido.estado = 'cancelado'
        pedido.save(update_fields=['estado'])

        logger.info(
            'Pedido %s cancelado por pago fallido.',
            pedido.numero_pedido
        )


def _extraer_pedido_id(payment_intent: dict) -> int | None:
    """Extrae el ID del pedido desde metadata de Stripe."""

    metadata = payment_intent.get('metadata', {})
    pedido_id = metadata.get('pedido_id')

    if not pedido_id:
        logger.warning(
            'Webhook: PaymentIntent sin pedido_id en metadata. ID: %s',
            payment_intent.get('id')
        )
        return None

    try:
        return int(pedido_id)

    except (ValueError, TypeError):
        logger.error(
            'Webhook: pedido_id inválido: %r',
            pedido_id
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
                pedido.numero_pedido
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
                'Stock decrementado: Producto %s, %s unidades.',
                producto_id,
                cantidad
            )

        else:
            logger.warning(
                'Producto %s: stock insuficiente para descontar %s unidades.',
                producto_id,
                cantidad
            )
