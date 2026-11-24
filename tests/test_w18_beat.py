"""Suite de pruebas W18 — Celery Beat y tarea de reporte diario.

Verifica la configuración del schedule, la ejecución de la tarea
y el envío del correo de reporte.

Ejecutar con:
    python manage.py test tests.test_w18_beat --verbosity=2

Resultado esperado:
    Ran 8 tests in X.XXXs
    OK
"""
from decimal import Decimal
from datetime import datetime, time, timedelta

from django.conf import settings
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from clientes.models      import Cliente
from configuracion.models import ConfiguracionERP
from productos.models     import Categoria, Producto
from ventas.models import DetalleVenta, Pedido, ReporteDiario, Venta
from ventas.tasks         import reporte_ventas_diario, verificar_stock_bajo

EMAIL_SETTINGS = {
    'EMAIL_BACKEND':               'django.core.mail.backends.locmem.EmailBackend',
    'CELERY_TASK_ALWAYS_EAGER':    True,
    'CELERY_TASK_EAGER_PROPAGATES': True,
    'ADMINS':           [('Admin Test', 'admin@test.com')],
    'DEFAULT_FROM_EMAIL': 'test@erp.com',
}


class BeatScheduleConfigTest(TestCase):
    """Verifica la configuración de CELERY_BEAT_SCHEDULE."""

    def test_beat_schedule_tiene_verificar_stock(self):
        """El schedule debe incluir verificar_stock_bajo."""
        schedule = settings.CELERY_BEAT_SCHEDULE
        tareas   = [v['task'] for v in schedule.values()]
        self.assertIn('ventas.verificar_stock_bajo', tareas)

    def test_beat_schedule_tiene_reporte_diario(self):
        """El schedule debe incluir reporte_ventas_diario."""
        schedule = settings.CELERY_BEAT_SCHEDULE
        tareas   = [v['task'] for v in schedule.values()]
        self.assertIn('ventas.reporte_ventas_diario', tareas)

    def test_reporte_usa_crontab(self):
        """El reporte diario debe usar crontab (no timedelta)."""
        from celery.schedules import crontab
        schedule = settings.CELERY_BEAT_SCHEDULE
        for nombre, config in schedule.items():
            if config['task'] == 'ventas.reporte_ventas_diario':
                self.assertIsInstance(
                    config['schedule'], crontab,
                    "reporte_ventas_diario debe usar crontab, no timedelta"
                )
                break

    def test_verificar_stock_usa_timedelta(self):
        """verificar_stock_bajo debe usar timedelta (intervalo)."""
        schedule = settings.CELERY_BEAT_SCHEDULE
        for nombre, config in schedule.items():
            if config['task'] == 'ventas.verificar_stock_bajo':
                self.assertIsInstance(
                    config['schedule'], timedelta,
                    "verificar_stock_bajo debe usar timedelta"
                )
                break


@override_settings(**EMAIL_SETTINGS)
class ReporteVentasTest(TestCase):
    """Tests de la tarea reporte_ventas_diario."""

    def setUp(self):
        mail.outbox = []

        ConfiguracionERP.get_instance()

        # Crear categoría.
        cat = Categoria.objects.create(
            nombre='Cat Rep'
        )

        # Crear producto.
        self.prod = Producto.objects.create(
            nombre='Producto Reporte',
            precio=Decimal('500.00'),
            stock=10,
            categoria=cat,
        )

        # Crear cliente.
        cli = Cliente.objects.create(
            nombre='Cliente Rep',
            correo='rep@test.com',
        )

        # Crear una venta interna.
        venta = Venta.objects.create(
            cliente=cli
        )

        DetalleVenta.objects.create(
            venta=venta,
            producto=self.prod,
            cantidad=3,
            precio_unitario=Decimal('500.00'),
        )

        # Crear un pedido en línea pagado.
        Pedido.objects.create(
            numero_pedido='PED-REP-001',
            cliente=cli,
            estado='pagado',
            total_pagado=Decimal('1500.00'),
        )

        # El reporte consulta el día anterior.
        fecha_ayer = timezone.localdate() - timedelta(days=1)

        fecha_reporte = timezone.make_aware(
            datetime.combine(fecha_ayer, time(12, 0))
        )

        # Ajustar la fecha de la venta interna.
        Venta.objects.filter(
            pk=venta.pk
        ).update(
            fecha=fecha_reporte
        )

        # Ajustar la fecha de pago del pedido.
        Pedido.objects.filter(
            numero_pedido='PED-REP-001'
        ).update(
            fecha_pago=fecha_reporte
        )

    def test_reporte_envia_correo_al_admin(self):
        """La tarea debe enviar correo al administrador."""
        reporte_ventas_diario.delay()
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('admin@test.com', mail.outbox[0].to)

    def test_reporte_asunto_contiene_fecha(self):
        """El asunto debe contener la fecha del día reportado."""
        reporte_ventas_diario.delay()
        fecha_reporte = timezone.localdate() - timezone.timedelta(days=1)
        fecha_str = fecha_reporte.strftime('%d/%m/%Y')
        self.assertIn(fecha_str, mail.outbox[0].subject)

    def test_reporte_sin_ventas_hoy_envia_correo(self):
        """Aunque no haya ventas, el reporte debe enviarse."""

        Pedido.objects.all().delete()
        Venta.objects.all().delete()

        reporte_ventas_diario.delay()

        self.assertEqual(len(mail.outbox), 1)

        cuerpo = mail.outbox[0].body
        self.assertIn('0', cuerpo)

    def test_reporte_devuelve_dict_con_totales(self):
        """Comprueba los totales de ambos canales y el reabasto."""
        resultado = reporte_ventas_diario.delay().get()

        self.assertIn('total_pedidos', resultado)
        self.assertIn('total_ventas', resultado)
        self.assertIn('total_facturado', resultado)
        self.assertIn('importe_pedidos', resultado)
        self.assertIn('importe_ventas', resultado)
        self.assertIn('total_operaciones', resultado)
        self.assertIn('top_productos', resultado)
        self.assertIn('productos_bajos', resultado)

        self.assertEqual(resultado['total_pedidos'], 1)
        self.assertEqual(resultado['total_ventas'], 1)
        self.assertEqual(resultado['total_operaciones'], 2)

        self.assertEqual(
            Decimal(resultado['total_facturado']),
            Decimal('3000.00')
        )
    def test_reporte_ya_enviado_no_duplica_correo(self):
        """Un reporte enviado no debe volver a mandar correo."""
        fecha_ayer = timezone.localdate() - timedelta(days=1)

        ReporteDiario.objects.create(
            fecha_reporte=fecha_ayer,
            estado='enviado',
            enviado_en=timezone.now(),
        )

        resultado = reporte_ventas_diario.delay().get()

        self.assertEqual(resultado['estado'], 'ya_enviado')
        self.assertEqual(len(mail.outbox), 0)

    def test_reporte_procesando_no_duplica_correo(self):
        """Un reporte en proceso reciente no debe duplicarse."""
        fecha_ayer = timezone.localdate() - timedelta(days=1)

        ReporteDiario.objects.create(
            fecha_reporte=fecha_ayer,
            estado='procesando',
        )

        resultado = reporte_ventas_diario.delay().get()

        self.assertEqual(resultado['estado'], 'ya_procesando')
        self.assertEqual(len(mail.outbox), 0)