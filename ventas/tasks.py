
# ventas/tasks.py
"""Tareas de la aplicación ventas.

W17: envío de correos mediante django-anymail + SendGrid.

El envío directo permite enviar confirmaciones sin depender de un
Celery Worker. La tarea Celery se conserva para instalaciones que
sí tengan un trabajador configurado.
"""

import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


def enviar_confirmacion_pedido_directo(pedido_id: int) -> dict:
    """
    Envía directamente la confirmación de un pedido.

    No necesita Redis ni un Celery Worker.

    La función evita volver a enviar un correo si el pedido ya está
    marcado como enviado.
    """
    from configuracion.models import ConfiguracionERP
    from ventas.models import Pedido

    try:
        pedido = Pedido.objects.select_related('cliente').get(pk=pedido_id)
    except Pedido.DoesNotExist:
        logger.error(
            '[correo_confirmacion] Pedido %s no existe.',
            pedido_id
        )
        return {
            'estado': 'error',
            'razon': 'Pedido no encontrado',
            'pedido_id': pedido_id,
        }

    # Evitar envíos duplicados cuando el correo ya fue registrado.
    if pedido.correo_enviado:
        logger.info(
            '[correo_confirmacion] Pedido %s: correo ya enviado. '
            'No se repetirá el envío.',
            pedido.numero_pedido
        )
        return {
            'estado': 'skip',
            'pedido_id': pedido_id,
            'razon': 'correo ya enviado',
        }

    config = ConfiguracionERP.get_instance()

    items = pedido.items_snapshot or []

    url_pedido = (
        'https://erp-django-njx2.onrender.com'
        f'/ventas/{pedido.pk}/'
    )

    contexto = {
        'pedido': pedido,
        'config': config,
        'items': items,
        'url_pedido': url_pedido,
    }

    asunto = (
        f'Confirmación de pedido {pedido.numero_pedido} '
        f'— {config.nombre_empresa}'
    )

    # Generar las versiones de texto y HTML.
    texto_plano = render_to_string(
        'emails/confirmacion_pedido.txt',
        contexto
    )

    html_body = render_to_string(
        'emails/confirmacion_pedido.html',
        contexto
    )

    correo_destino = pedido.cliente.correo
    correo_origen = settings.DEFAULT_FROM_EMAIL

    if not correo_destino:
        raise ValueError(
            f'El pedido {pedido.numero_pedido} no tiene '
            'un correo electrónico de destino.'
        )

    if not correo_origen:
        raise ValueError(
            'DEFAULT_FROM_EMAIL no está configurado.'
        )

    mensaje = EmailMultiAlternatives(
        subject=asunto,
        body=texto_plano,
        from_email=correo_origen,
        to=[correo_destino],
    )

    mensaje.attach_alternative(html_body, 'text/html')

    try:
        # Enviar usando el backend configurado en Django.
        enviados = mensaje.send(fail_silently=False)

        if enviados != 1:
            raise RuntimeError(
                'El backend de correo no confirmó el envío.'
            )

        # Marcar como enviado después de que el backend acepte el correo.
        pedido.correo_enviado = True
        pedido.save(update_fields=['correo_enviado'])

        logger.info(
            '[correo_confirmacion] Correo aceptado por el backend '
            'para %s. Pedido: %s.',
            correo_destino,
            pedido.numero_pedido
        )

        return {
            'estado': 'ok',
            'pedido_id': pedido_id,
            'correo': correo_destino,
        }

    except Exception:
        logger.exception(
            '[correo_confirmacion] Error al enviar el correo '
            'del pedido %s.',
            pedido.numero_pedido
        )
        raise


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name='ventas.enviar_confirmacion_pedido',
)
def enviar_confirmacion_pedido(self, pedido_id: int) -> dict:
    """
    Tarea Celery para enviar la confirmación.

    Se conserva para cuando exista un Celery Worker.
    """
    try:
        return enviar_confirmacion_pedido_directo(pedido_id)

    except Exception as exc:
        logger.exception(
            '[correo_confirmacion] Error en tarea Celery para pedido %s.',
            pedido_id
        )

        raise self.retry(
            exc=exc,
            countdown=60 * (self.request.retries + 1)
        )


@shared_task(
    bind=True,
    max_retries=1,
    name='ventas.verificar_stock_bajo',
)
def verificar_stock_bajo(self, umbral: int = 5) -> dict:
    """
    Verifica productos con stock bajo y envía una alerta al administrador.
    """
    from productos.models import Producto

    productos_bajos = list(
        Producto.objects
        .select_related('categoria')
        .filter(activo=True, stock__lt=umbral)
        .values(
            'pk',
            'nombre',
            'stock',
            'categoria__nombre'
        )
        .order_by('stock')
    )

    if not productos_bajos:
        logger.info(
            '[stock_bajo] Todos los productos tienen stock >= %s. OK.',
            umbral
        )
        return {
            'umbral': umbral,
            'total': 0,
            'productos_bajos': [],
        }

    logger.warning(
        '[stock_bajo] %s producto(s) con stock inferior a %s.',
        len(productos_bajos),
        umbral
    )

    if settings.ADMINS:
        _enviar_alerta_stock(productos_bajos, umbral)

    return {
        'umbral': umbral,
        'total': len(productos_bajos),
        'productos_bajos': productos_bajos,
    }


def _enviar_alerta_stock(
    productos_bajos: list,
    umbral: int
) -> None:
    """Envía el correo de alerta de stock al primer administrador."""

    from configuracion.models import ConfiguracionERP

    config = ConfiguracionERP.get_instance()
    fecha = timezone.now().strftime('%d/%m/%Y %H:%M')

    url_admin = (
        'https://erp-django-njx2.onrender.com'
        '/admin/productos/producto/'
    )

    contexto = {
        'productos_bajos': productos_bajos,
        'total_productos': len(productos_bajos),
        'umbral': umbral,
        'fecha': fecha,
        'url_admin': url_admin,
        'config': config,
    }

    asunto = (
        f'[ALERTA] {len(productos_bajos)} producto(s) '
        f'con stock inferior a {umbral}'
    )

    texto_plano = render_to_string(
        'emails/alerta_stock.txt',
        contexto
    )

    html_body = render_to_string(
        'emails/alerta_stock.html',
        contexto
    )

    admin_nombre, admin_correo = settings.ADMINS[0]

    mensaje = EmailMultiAlternatives(
        subject=asunto,
        body=texto_plano,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[admin_correo],
    )

    mensaje.attach_alternative(html_body, 'text/html')

    try:
        enviados = mensaje.send(fail_silently=False)

        logger.info(
            '[stock_bajo] Resultado del envío: %s. '
            'Destinatario: %s. Productos: %s.',
            enviados,
            admin_correo,
            len(productos_bajos)
        )

    except Exception:
        logger.exception(
            '[stock_bajo] Error al enviar la alerta al administrador.'
        )
