
"""
Tareas de la aplicación ventas.

W17: envío de correos mediante django-anymail + SendGrid.

El envío directo permite enviar confirmaciones sin depender de un
Celery Worker. La tarea Celery se conserva para instalaciones que
sí tengan un trabajador configurado.

W18: reporte diario de ventas y verificación de stock bajo.
"""

import logging
from decimal import Decimal, InvalidOperation

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


# =========================================================
# W17 - CONFIRMACIÓN DE PEDIDOS
# =========================================================

def enviar_confirmacion_pedido_directo(pedido_id: int) -> dict:
    """Envía directamente la confirmación de un pedido."""
    from configuracion.models import ConfiguracionERP
    from ventas.models import Pedido

    try:
        pedido = Pedido.objects.select_related('cliente').get(pk=pedido_id)
    except Pedido.DoesNotExist:
        logger.error(
            '[correo_confirmacion] Pedido %s no existe.',
            pedido_id,
        )
        return {
            'estado': 'error',
            'razon': 'Pedido no encontrado',
            'pedido_id': pedido_id,
        }

    if pedido.correo_enviado:
        logger.info(
            '[correo_confirmacion] Pedido %s: correo ya enviado.',
            pedido.numero_pedido,
        )
        return {
            'estado': 'skip',
            'pedido_id': pedido_id,
            'razon': 'correo ya enviado',
        }

    config = ConfiguracionERP.get_instance()

    items_correo = []

    for item in pedido.items_snapshot or []:
        item_correo = dict(item)

        cantidad = Decimal(str(item_correo.get('cantidad', 0)))
        precio = Decimal(str(item_correo.get('precio', 0)))

        item_correo['subtotal'] = (
            cantidad * precio
        ).quantize(Decimal('0.01'))

        items_correo.append(item_correo)

    url_pedido = (
        'https://erp-django-njx2.onrender.com'
        f'/ventas/{pedido.pk}/'
    )

    contexto = {
        'pedido': pedido,
        'config': config,
        'items': items_correo,
        'url_pedido': url_pedido,
    }

    asunto = (
        f'Confirmación de pedido {pedido.numero_pedido} '
        f'— {config.nombre_empresa}'
    )

    texto_plano = render_to_string(
        'emails/confirmacion_pedido.txt',
        contexto,
    )

    html_body = render_to_string(
        'emails/confirmacion_pedido.html',
        contexto,
    )

    correo_destino = pedido.cliente.correo
    correo_origen = settings.DEFAULT_FROM_EMAIL

    if not correo_destino:
        raise ValueError(
            f'El pedido {pedido.numero_pedido} no tiene '
            'un correo electrónico de destino.'
        )

    if not correo_origen:
        raise ValueError('DEFAULT_FROM_EMAIL no está configurado.')

    mensaje = EmailMultiAlternatives(
        subject=asunto,
        body=texto_plano,
        from_email=correo_origen,
        to=[correo_destino],
    )

    mensaje.attach_alternative(html_body, 'text/html')

    try:
        enviados = mensaje.send(fail_silently=False)

        if enviados != 1:
            raise RuntimeError(
                'El backend de correo no confirmó el envío.'
            )

        pedido.correo_enviado = True
        pedido.save(update_fields=['correo_enviado'])

        logger.info(
            '[correo_confirmacion] Correo aceptado para %s. Pedido: %s.',
            correo_destino,
            pedido.numero_pedido,
        )

        return {
            'estado': 'ok',
            'pedido_id': pedido_id,
            'correo': correo_destino,
        }

    except Exception:
        logger.exception(
            '[correo_confirmacion] Error al enviar el correo del pedido %s.',
            pedido.numero_pedido,
        )
        raise


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name='ventas.enviar_confirmacion_pedido',
)
def enviar_confirmacion_pedido(self, pedido_id: int) -> dict:
    """Tarea Celery para enviar la confirmación."""
    try:
        return enviar_confirmacion_pedido_directo(pedido_id)
    except Exception as exc:
        logger.exception(
            '[correo_confirmacion] Error en tarea Celery para pedido %s.',
            pedido_id,
        )
        raise self.retry(
            exc=exc,
            countdown=60 * (self.request.retries + 1),
        )


# =========================================================
# W17 - ALERTAS DE INVENTARIO
# =========================================================

@shared_task(
    bind=True,
    max_retries=1,
    default_retry_delay=60,
    name='ventas.verificar_stock_bajo',
)
def verificar_stock_bajo(self, umbral: int = 5) -> dict:
    """
    Verifica productos activos con stock inferior al umbral
    y envía una alerta por correo a los administradores.
    """
    from productos.models import Producto

    if umbral < 0:
        raise ValueError('El umbral no puede ser negativo.')

    productos_bajos = list(
        Producto.objects
        .filter(
            activo=True,
            stock__lt=umbral,
        )
        .select_related('categoria')
        .order_by('stock', 'nombre')
        .values(
            'pk',
            'nombre',
            'stock',
            'categoria__nombre',
        )
    )

    if not productos_bajos:
        logger.info(
            '[stock_bajo] Todos los productos tienen stock >= %s. OK.',
            umbral,
        )
        return {
            'estado': 'sin_productos',
            'umbral': umbral,
            'total': 0,
            'productos_bajos': [],
        }

    logger.warning(
        '[stock_bajo] %s producto(s) con stock inferior a %s.',
        len(productos_bajos),
        umbral,
    )

    destinatarios = getattr(
        settings,
        'ALERTA_STOCK_DESTINATARIOS',
        [],
    )

    if not destinatarios:
        logger.error(
            '[stock_bajo] No hay destinatarios configurados.',
        )
        return {
            'estado': 'sin_destinatarios',
            'umbral': umbral,
            'total': len(productos_bajos),
            'productos_bajos': productos_bajos,
        }

    try:
        _enviar_alerta_stock(productos_bajos, umbral)
    except Exception as exc:
        logger.exception(
            '[stock_bajo] Error al enviar la alerta de inventario.',
        )
        raise self.retry(exc=exc, countdown=60)

    return {
        'estado': 'alerta_enviada',
        'umbral': umbral,
        'total': len(productos_bajos),
        'productos_bajos': productos_bajos,
        'destinatarios': destinatarios,
    }


def _enviar_alerta_stock(
    productos_bajos: list,
    umbral: int,
) -> None:
    """Envía una alerta de inventario a los destinatarios configurados."""
    from configuracion.models import ConfiguracionERP

    destinatarios = getattr(
        settings,
        'ALERTA_STOCK_DESTINATARIOS',
        [],
    )

    if not destinatarios:
        raise ValueError(
            'No hay destinatarios configurados para las alertas de inventario.'
        )

    config = ConfiguracionERP.get_instance()

    fecha = timezone.localtime().strftime('%d/%m/%Y %H:%M')

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
        contexto,
    )

    html_body = render_to_string(
        'emails/alerta_stock.html',
        contexto,
    )

    mensaje = EmailMultiAlternatives(
        subject=asunto,
        body=texto_plano,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=destinatarios,
    )

    mensaje.attach_alternative(html_body, 'text/html')

    enviados = mensaje.send(fail_silently=False)

    if enviados != 1:
        raise RuntimeError(
            'El backend de correo no confirmó el envío de la alerta.'
        )

    logger.info(
        '[stock_bajo] Alerta enviada. Destinatarios: %s. Productos: %s.',
        ', '.join(destinatarios),
        len(productos_bajos),
    )


# =========================================================
# W18 - REPORTE DIARIO DE VENTAS
# =========================================================

@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=300,
    name='ventas.reporte_ventas_diario',
)
def reporte_ventas_diario(self) -> dict:
    """
    Envía el reporte del día anterior con:

    - Pedidos pagados del checkout en línea.
    - Ventas internas del módulo de ventas.
    - Ingresos separados y total combinado.
    - Productos más vendidos de ambos canales.
    - Productos activos con menos de 5 unidades.
    - Inventario completo de productos activos e inactivos.
    """
    from datetime import datetime, time, timedelta

    from configuracion.models import ConfiguracionERP
    from productos.models import Producto
    from ventas.models import Pedido, ReporteDiario, Venta

    hoy = timezone.localdate()
    fecha_reporte = hoy - timedelta(days=1)

    inicio = timezone.make_aware(
        datetime.combine(fecha_reporte, time.min)
    )
    fin = inicio + timedelta(days=1)

    config = ConfiguracionERP.get_instance()

    # -----------------------------------------------------
    # 1. PEDIDOS EN LÍNEA
    # -----------------------------------------------------

    pedidos = list(
        Pedido.objects
        .filter(
            fecha_pago__gte=inicio,
            fecha_pago__lt=fin,
            estado__in=['pagado', 'enviado', 'entregado'],
        )
        .select_related('cliente')
        .order_by('fecha_pago', 'pk')
    )

    total_pedidos = len(pedidos)

    importe_pedidos = sum(
        (
            pedido.total_pagado or Decimal('0.00')
            for pedido in pedidos
        ),
        Decimal('0.00'),
    )

    pedidos_detalle = []
    productos = {}

    def acumular_producto(nombre, cantidad, precio, producto_id=None):
        """Agrupa unidades e ingresos por producto."""
        try:
            cantidad = int(cantidad)
            precio = Decimal(str(precio))
        except (ValueError, TypeError, InvalidOperation):
            return

        if cantidad <= 0 or precio < 0:
            return

        nombre = str(nombre or 'Producto sin nombre')

        clave = (
            producto_id
            if producto_id is not None
            else nombre.strip().casefold()
        )

        if clave not in productos:
            productos[clave] = {
                'nombre': nombre,
                'unidades': 0,
                'ingreso': Decimal('0.00'),
            }

        productos[clave]['unidades'] += cantidad
        productos[clave]['ingreso'] += precio * cantidad

    for pedido in pedidos:
        items_pedido = []

        for item in pedido.items_snapshot or []:
            nombre = item.get('nombre', 'Producto sin nombre')
            cantidad = item.get('cantidad', 0)
            precio = item.get(
                'precio',
                item.get('precio_unitario', '0'),
            )

            try:
                subtotal = (
                    Decimal(str(precio)) * int(cantidad)
                ).quantize(Decimal('0.01'))
            except (ValueError, TypeError, InvalidOperation):
                subtotal = Decimal('0.00')

            items_pedido.append({
                'nombre': nombre,
                'cantidad': cantidad,
                'precio': precio,
                'subtotal': subtotal,
            })

            acumular_producto(
                nombre=nombre,
                cantidad=cantidad,
                precio=precio,
                producto_id=item.get('producto_id'),
            )

        pedidos_detalle.append({
            'numero': pedido.numero_pedido,
            'cliente': str(pedido.cliente),
            'fecha': (
                timezone.localtime(pedido.fecha_pago).strftime('%H:%M')
                if pedido.fecha_pago
                else ''
            ),
            'total': pedido.total_pagado or Decimal('0.00'),
            'items': items_pedido,
        })

    # -----------------------------------------------------
    # 2. VENTAS INTERNAS
    # -----------------------------------------------------

    ventas = list(
        Venta.objects
        .filter(
            fecha__gte=inicio,
            fecha__lt=fin,
        )
        .select_related('cliente')
        .prefetch_related('detalles__producto')
        .order_by('fecha', 'pk')
    )

    ventas_detalle = []
    importe_ventas = Decimal('0.00')

    for venta in ventas:
        items_venta = []
        total_venta = Decimal('0.00')

        for detalle in venta.detalles.all():
            subtotal = (
                detalle.precio_unitario * detalle.cantidad
            ).quantize(Decimal('0.01'))

            total_venta += subtotal

            nombre = detalle.producto.nombre

            items_venta.append({
                'nombre': nombre,
                'cantidad': detalle.cantidad,
                'precio': detalle.precio_unitario,
                'subtotal': subtotal,
            })

            acumular_producto(
                nombre=nombre,
                cantidad=detalle.cantidad,
                precio=detalle.precio_unitario,
                producto_id=detalle.producto_id,
            )

        importe_ventas += total_venta

        ventas_detalle.append({
            'numero': venta.pk,
            'cliente': str(venta.cliente),
            'fecha': timezone.localtime(venta.fecha).strftime('%H:%M'),
            'total': total_venta,
            'items': items_venta,
        })

    total_ventas = len(ventas)

    # -----------------------------------------------------
    # 3. PRODUCTOS MÁS VENDIDOS
    # -----------------------------------------------------

    top_productos = sorted(
        productos.values(),
        key=lambda producto: producto['ingreso'],
        reverse=True,
    )[:5]

    top_productos_resultado = [
        {
            'nombre': producto['nombre'],
            'unidades': producto['unidades'],
            'ingreso': str(producto['ingreso']),
        }
        for producto in top_productos
    ]

    # -----------------------------------------------------
    # 4. PRODUCTOS QUE NECESITAN REABASTO
    # -----------------------------------------------------

    umbral_stock = 5

    productos_bajos = list(
        Producto.objects
        .filter(
            activo=True,
            stock__lt=umbral_stock,
        )
        .select_related('categoria')
        .order_by('stock', 'nombre')
        .values(
            'pk',
            'nombre',
            'stock',
            'categoria__nombre',
        )
    )

    # -----------------------------------------------------
    # 5. INVENTARIO COMPLETO
    # -----------------------------------------------------

    inventario = list(
        Producto.objects
        .select_related('categoria')
        .order_by('nombre')
        .values(
            'pk',
            'nombre',
            'precio',
            'stock',
            'activo',
            'categoria__nombre',
        )
    )

    inventario_detalle = []
    total_unidades_inventario = 0
    valor_total_inventario = Decimal('0.00')
    total_activos = 0
    total_inactivos = 0

    for producto in inventario:
        precio = Decimal(str(producto['precio'] or '0.00'))
        stock = int(producto['stock'] or 0)
        valor = precio * stock

        total_unidades_inventario += stock
        valor_total_inventario += valor

        if producto['activo']:
            total_activos += 1
            estado_producto = 'Activo'
        else:
            total_inactivos += 1
            estado_producto = 'Inactivo'

        inventario_detalle.append({
            **producto,
            'valor_inventario': valor,
            'estado': estado_producto,
        })

    # -----------------------------------------------------
    # 6. RESUMEN GENERAL
    # -----------------------------------------------------

    total_facturado = importe_pedidos + importe_ventas
    total_operaciones = total_pedidos + total_ventas

    resultado = {
        'estado': 'pendiente',
        'fecha': str(fecha_reporte),
        'total_pedidos': total_pedidos,
        'importe_pedidos': str(importe_pedidos),
        'total_ventas': total_ventas,
        'importe_ventas': str(importe_ventas),
        'total_operaciones': total_operaciones,
        'total_facturado': str(total_facturado),
        'top_productos': top_productos_resultado,
        'total_productos_bajos': len(productos_bajos),
        'productos_bajos': productos_bajos,
        'inventario': inventario_detalle,
        'total_productos_inventario': len(inventario_detalle),
        'total_activos': total_activos,
        'total_inactivos': total_inactivos,
        'total_unidades_inventario': total_unidades_inventario,
        'valor_total_inventario': str(valor_total_inventario),
    }

    logger.info(
        '[reporte_diario] %s: %s pedidos, %s ventas internas, '
        '$%s facturados y %s productos por reabastecer.',
        fecha_reporte,
        total_pedidos,
        total_ventas,
        total_facturado,
        len(productos_bajos),
    )


    # -----------------------------------------------------
    # 7. CONTROL DE DUPLICADOS, DESTINATARIO Y ENVÍO
    # -----------------------------------------------------

    ahora = timezone.now()

    # Reservar el reporte de forma segura.
    with transaction.atomic():
        registro, creado = ReporteDiario.objects.get_or_create(
            fecha_reporte=fecha_reporte,
        )

        registro = (
            ReporteDiario.objects
            .select_for_update()
            .get(pk=registro.pk)
        )

        # Si ya se envió, no repetir el correo.
        if registro.estado == 'enviado':
            resultado['estado'] = 'ya_enviado'
            logger.info(
                '[reporte_diario] El reporte del %s ya fue enviado.',
                fecha_reporte,
            )
            return resultado

        # Evitar dos envíos simultáneos.
        if (
            registro.estado == 'procesando'
            and registro.actualizado >= ahora - timedelta(hours=2)
        ):
            resultado['estado'] = 'ya_procesando'
            logger.warning(
                '[reporte_diario] El reporte del %s ya está procesándose.',
                fecha_reporte,
            )
            return resultado

        registro.estado = 'procesando'
        registro.intentos += 1
        registro.detalle_error = ''
        registro.save(
            update_fields=[
                'estado',
                'intentos',
                'detalle_error',
                'actualizado',
            ]
        )

    # Validar destinatario.
    if not settings.ADMINS or not settings.ADMINS[0][1]:
        mensaje = 'No hay administrador con correo configurado.'

        ReporteDiario.objects.filter(pk=registro.pk).update(
            estado='error',
            detalle_error=mensaje,
        )

        resultado['estado'] = 'sin_destinatario'
        logger.error('[reporte_diario] %s', mensaje)
        return resultado

    try:
        _enviar_reporte_ventas(
            fecha=fecha_reporte,
            total_pedidos=total_pedidos,
            importe_pedidos=importe_pedidos,
            pedidos_detalle=pedidos_detalle,
            total_ventas=total_ventas,
            importe_ventas=importe_ventas,
            ventas_detalle=ventas_detalle,
            total_operaciones=total_operaciones,
            total_facturado=total_facturado,
            top_productos=top_productos,
            productos_bajos=productos_bajos,
            inventario=inventario_detalle,
            total_productos_inventario=len(inventario_detalle),
            total_activos=total_activos,
            total_inactivos=total_inactivos,
            total_unidades_inventario=total_unidades_inventario,
            valor_total_inventario=valor_total_inventario,
            umbral_stock=umbral_stock,
            config=config,
        )

        # Registrar el envío confirmado por el backend de correo.
        ReporteDiario.objects.filter(pk=registro.pk).update(
            estado='enviado',
            enviado_en=timezone.now(),
            detalle_error='',
        )

        resultado['estado'] = 'enviado'

    except Exception as exc:
        logger.exception(
            '[reporte_diario] Falló el envío del reporte.'
        )

        ReporteDiario.objects.filter(pk=registro.pk).update(
            estado='error',
            detalle_error=str(exc),
        )

        raise self.retry(exc=exc)

    return resultado

def _enviar_reporte_ventas(
    fecha,
    total_pedidos,
    importe_pedidos,
    pedidos_detalle,
    total_ventas,
    importe_ventas,
    ventas_detalle,
    total_operaciones,
    total_facturado,
    top_productos,
    productos_bajos,
    inventario,
    total_productos_inventario,
    total_activos,
    total_inactivos,
    total_unidades_inventario,
    valor_total_inventario,
    umbral_stock,
    config,
) -> None:
    """Envía el reporte diario al primer administrador configurado."""

    admin_nombre, admin_correo = settings.ADMINS[0]

    if not admin_correo:
        raise ValueError(
            'El administrador no tiene correo configurado.'
        )

    url_admin = (
        'https://erp-django-njx2.onrender.com'
        '/admin/ventas/pedido/'
    )

    fecha_str = fecha.strftime('%d/%m/%Y')

    contexto = {
        'fecha': fecha_str,
        'hora_generacion': timezone.localtime().strftime('%H:%M'),
        'config': config,
        'admin_nombre': admin_nombre,
        'total_pedidos': total_pedidos,
        'importe_pedidos': importe_pedidos,
        'pedidos_detalle': pedidos_detalle,
        'total_ventas': total_ventas,
        'importe_ventas': importe_ventas,
        'ventas_detalle': ventas_detalle,
        'total_operaciones': total_operaciones,
        'total_facturado': total_facturado,
        'top_productos': top_productos,
        'productos_bajos': productos_bajos,
        'total_productos_bajos': len(productos_bajos),
        'umbral_stock': umbral_stock,
        'url_admin': url_admin,

        # Inventario completo
        'inventario': inventario,
        'total_productos_inventario': total_productos_inventario,
        'total_activos': total_activos,
        'total_inactivos': total_inactivos,
        'total_unidades_inventario': total_unidades_inventario,
        'valor_total_inventario': valor_total_inventario,
    }

    asunto = (
        f'Reporte diario de ventas del {fecha_str} '
        f'— {config.nombre_empresa}'
    )

    texto_plano = render_to_string(
        'emails/reporte_ventas.txt',
        contexto,
    )

    html_body = render_to_string(
        'emails/reporte_ventas.html',
        contexto,
    )

    mensaje = EmailMultiAlternatives(
        subject=asunto,
        body=texto_plano,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[admin_correo],
    )

    mensaje.attach_alternative(html_body, 'text/html')

    enviados = mensaje.send(fail_silently=False)

    if enviados != 1:
        raise RuntimeError(
            'El backend de correo no confirmó el envío del reporte diario.'
        )

    logger.info(
        '[reporte_diario] Correo aceptado por el backend para %s.',
        admin_correo,
    )
