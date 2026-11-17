# catalogo/checkout_utils.py
"""Funciones auxiliares para el proceso de checkout — W14.

Separadas de views.py para facilitar las pruebas unitarias.
"""
from decimal import ROUND_HALF_UP, Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone

from clientes.models import Cliente
from configuracion.models import ConfiguracionERP
from ventas.models import Pedido

CENTAVOS = Decimal('0.01')


def calcular_totales(carrito: dict) -> dict:
    """Calcula subtotal, IVA y total del carrito.

    Args:
        carrito: dict de sesión con estructura
                 {str(pk): {precio: str, cantidad: int, ...}}

    Returns:
        dict con subtotal, iva_pct, iva_monto, total (todos Decimal).
    """
    config = ConfiguracionERP.get_instance()
    iva_porcentaje = Decimal(str(config.iva_porcentaje))
    iva_factor = iva_porcentaje / Decimal('100')

    subtotal = sum(
        (
            Decimal(datos['precio']) * int(datos['cantidad'])
            for datos in carrito.values()
        ),
        Decimal('0.00'),
    ).quantize(CENTAVOS, rounding=ROUND_HALF_UP)

    iva_monto = (subtotal * iva_factor).quantize(
        CENTAVOS, rounding=ROUND_HALF_UP
    )
    total = subtotal + iva_monto

    return {
        'subtotal':  subtotal,
        'iva_pct':   iva_porcentaje,
        'iva_monto': iva_monto,
        'total':     total,
    }


def armar_items(carrito: dict) -> list:
    """Convierte el carrito de sesión en una lista con el subtotal por línea.

    Los templates de Django no pueden multiplicar (precio × cantidad),
    por eso el cálculo se hace aquí.

    Returns:
        list de dicts con prod_id, nombre, precio, cantidad, subtotal
        (Decimal) e imagen.
    """
    items = []
    for prod_id, datos in carrito.items():
        precio = Decimal(datos['precio'])
        cantidad = int(datos['cantidad'])
        items.append({
            'prod_id':  prod_id,
            'nombre':   datos['nombre'],
            'precio':   precio,
            'cantidad': cantidad,
            'subtotal': precio * cantidad,
            'imagen':   datos.get('imagen'),
        })
    return items


def obtener_o_crear_cliente(user) -> Cliente:
    """Obtiene o crea un Cliente del ERP vinculado al usuario Django.

    Usa el correo del usuario si existe; si no, genera uno temporal.
    La búsqueda no distingue mayúsculas y tolera correos duplicados
    (devuelve el cliente más antiguo).

    Args:
        user: instancia de django.contrib.auth.models.User.

    Returns:
        Cliente: instancia del modelo Cliente del ERP.
    """
    correo = (user.email or f'{user.username}@erp.local').strip().lower()
    nombre_completo = user.get_full_name().strip()
    nombre = nombre_completo or user.username

    cliente = (
        Cliente.objects
        .filter(correo__iexact=correo)
        .order_by('pk')
        .first()
    )

    if cliente is None:
        try:
            with transaction.atomic():
                cliente = Cliente.objects.create(
                    correo=correo, nombre=nombre, activo=True
                )
        except IntegrityError:
            # Otra petición lo creó al mismo tiempo: lo recuperamos.
            cliente = (
                Cliente.objects
                .filter(correo__iexact=correo)
                .order_by('pk')
                .first()
            )
            if cliente is None:
                raise
        return cliente

    # Actualizar nombre si el usuario tiene nombre completo
    if nombre_completo and cliente.nombre != nombre_completo:
        cliente.nombre = nombre_completo
        cliente.save(update_fields=['nombre'])

    return cliente


def generar_numero_pedido() -> str:
    """Genera un número de pedido único con formato PED-YYYY-NNNN.

    Busca el consecutivo más alto existente para el año actual
    y genera el siguiente número disponible.
    """
    anio = timezone.localdate().year
    prefijo = f'PED-{anio}-'

    numeros_existentes = Pedido.objects.filter(
        numero_pedido__startswith=prefijo
    ).values_list('numero_pedido', flat=True)

    consecutivos = []

    for numero in numeros_existentes:
        sufijo = numero[len(prefijo):]

        if sufijo.isdigit():
            consecutivos.append(int(sufijo))

    siguiente = max(consecutivos, default=0) + 1
    numero_pedido = f'{prefijo}{siguiente:04d}'

    while Pedido.objects.filter(numero_pedido=numero_pedido).exists():
        siguiente += 1
        numero_pedido = f'{prefijo}{siguiente:04d}'

    return numero_pedido