
"""Suite de pruebas W16 — Celery worker y tareas asíncronas.

Verifica la configuración de Celery, la definición de las tareas,
la confirmación de pedidos y su programación desde el webhook.

Ejecutar con:
    python manage.py test tests.test_w16_celery --verbosity=2

Resultado esperado:
    Ran 8 tests in X.XXXs
    OK
"""

from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from clientes.models import Cliente
from configuracion.models import ConfiguracionERP
from productos.models import Categoria, Producto
from ventas.models import Pedido
from ventas.tasks import (
    enviar_confirmacion_pedido,
    verificar_stock_bajo,
)


class CeleryConfigTest(TestCase):
    """Verifica que Celery está correctamente configurado."""

    def test_celery_app_importable(self):
        """La app Celery debe poder importarse sin errores."""
        from core.celery import app as celery_app

        self.assertIsNotNone(celery_app)
        self.assertEqual(celery_app.main, 'core')

    def test_tareas_registradas_en_celery(self):
        """Las tareas de ventas deben estar registradas en Celery."""
        from core.celery import app as celery_app

        tareas = celery_app.tasks.keys()

        self.assertIn(
            'ventas.enviar_confirmacion_pedido',
            tareas,
        )
        self.assertIn(
            'ventas.verificar_stock_bajo',
            tareas,
        )


class EnviarConfirmacionTareaTest(TestCase):
    """Tests de las tareas asíncronas de ventas."""

    def setUp(self):
        ConfiguracionERP.get_instance()

        categoria = Categoria.objects.create(nombre='Cat')

        Producto.objects.create(
            nombre='P',
            precio=Decimal('100.00'),
            stock=5,
            categoria=categoria,
        )

        cliente = Cliente.objects.create(
            nombre='C',
            correo='c@t.com',
        )

        self.pedido = Pedido.objects.create(
            numero_pedido='PED-2025-0001',
            cliente=cliente,
            estado='pagado',
            total_pagado=Decimal('116.00'),
            items_snapshot=[],
        )

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_tarea_ejecuta_y_retorna_ok(self):
        """La tarea debe ejecutarse y retornar estado 'ok'."""

        resultado = enviar_confirmacion_pedido.delay(
            self.pedido.pk
        )

        data = resultado.get()

        self.assertEqual(data['estado'], 'ok')
        self.assertEqual(data['pedido_id'], self.pedido.pk)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_tarea_con_pedido_inexistente_retorna_error(self):
        """La tarea con pedido inexistente debe retornar estado 'error'."""

        resultado = enviar_confirmacion_pedido.delay(9999)

        data = resultado.get()

        self.assertEqual(data['estado'], 'error')

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_verificar_stock_bajo_detecta_productos(self):
        """verificar_stock_bajo debe detectar productos bajo el umbral."""

        Producto.objects.filter(nombre='P').update(stock=3)

        resultado = verificar_stock_bajo.delay(umbral=5)

        data = resultado.get()

        self.assertGreaterEqual(data['total'], 1)

        nombres = [
            producto['nombre']
            for producto in data['productos_bajos']
        ]

        self.assertIn('P', nombres)


class TareaInvocadaDesdeVistaTest(TestCase):
    """Verifica la confirmación del pago y la programación de Celery."""

    def setUp(self):
        ConfiguracionERP.get_instance()

        cliente = Cliente.objects.create(
            nombre='C',
            correo='test@test.com',
        )

        self.pedido = Pedido.objects.create(
            numero_pedido='PED-2025-VISTA',
            cliente=cliente,
            estado='pendiente',
            total_pagado=Decimal('100.00'),
            items_snapshot=[],
        )

    def preparar_carrito(self):
        """Prepara el carrito de prueba en la sesión."""

        session = self.client.session

        session['carrito'] = {
            '1': {
                'nombre': 'Producto prueba',
                'precio': '100.00',
                'cantidad': 1,
            }
        }

        session['pedido_pendiente_id'] = self.pedido.pk
        session.save()

    def test_pago_pendiente_no_vacia_carrito(self):
        """Un pedido pendiente no debe mostrarse como pagado."""

        self.preparar_carrito()

        response = self.client.get(
            reverse(
                'catalogo:pago_exitoso',
                args=[self.pedido.pk],
            )
        )

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response,
            'catalogo/pago_pendiente.html',
        )

        session = self.client.session

        self.assertIn('1', session['carrito'])

        self.assertEqual(
            session['pedido_pendiente_id'],
            self.pedido.pk,
        )

    def test_pago_confirmado_vacia_carrito(self):
        """Un pedido pagado permite mostrar la confirmación."""

        self.pedido.estado = 'pagado'
        self.pedido.save(update_fields=['estado'])

        self.preparar_carrito()

        response = self.client.get(
            reverse(
                'catalogo:pago_exitoso',
                args=[self.pedido.pk],
            )
        )

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response,
            'catalogo/pago_exitoso.html',
        )

        session = self.client.session

        self.assertEqual(session['carrito'], {})

        self.assertNotIn(
            'pedido_pendiente_id',
            session,
        )

    def test_webhook_succeeded_programa_celery_una_sola_vez(self):
        """El webhook programa Celery una vez y evita duplicados."""

        evento = {
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'id': 'pi_test',
                    'metadata': {
                        'pedido_id': str(self.pedido.pk),
                    },
                },
            },
        }

        with (
            patch(
                'catalogo.webhook_views.stripe.Webhook.construct_event'
            ) as mock_event,
            patch(
                'ventas.tasks.enviar_confirmacion_pedido.delay'
            ) as mock_delay,
        ):
            mock_event.return_value = evento

            # Primer evento: confirma el pedido y programa Celery.
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(
                    reverse('catalogo:webhook'),
                    data=b'{}',
                    content_type='application/json',
                    HTTP_STRIPE_SIGNATURE='t=1,v1=ok',
                )

            self.assertEqual(response.status_code, 200)

            self.pedido.refresh_from_db()

            self.assertEqual(
                self.pedido.estado,
                'pagado',
            )

            mock_delay.assert_called_once_with(
                self.pedido.pk
            )

            # Segundo evento: no debe programar otra tarea.
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(
                    reverse('catalogo:webhook'),
                    data=b'{}',
                    content_type='application/json',
                    HTTP_STRIPE_SIGNATURE='t=1,v1=ok',
                )

            self.assertEqual(response.status_code, 200)

            mock_delay.assert_called_once_with(
                self.pedido.pk
            )
