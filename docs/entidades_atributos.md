
# Entidades y Atributos — ERP Django
## Espiral 2 · W04 · Modelado de Datos

Este documento define las ocho entidades del ERP,
sus atributos, tipos de dato, restricciones y justificaciones.

## 1. Categoria

| Atributo | Tipo Django | Restricción | Justificación |
|---|---|---|---|
| id | BigAutoField | PK, auto | Identificador generado automáticamente |
| nombre | CharField(100) | unique, not null | Evita categorías duplicadas |
| descripcion | TextField | blank=True | Descripción opcional |

## 2. Proveedor

| Atributo | Tipo Django | Restricción | Justificación |
|---|---|---|---|
| id | BigAutoField | PK, auto | Identificador automático |
| nombre | CharField(150) | not null | Nombre comercial |
| contacto | CharField(100) | blank=True | Persona de contacto opcional |
| correo | EmailField | unique, not null | Correo único del proveedor |
| telefono | CharField(20) | blank=True | Teléfono opcional |
| activo | BooleanField | default=True | Permite desactivar sin borrar |
| creado | DateTimeField | auto_now_add | Registra la fecha de creación |

## 3. Cliente

| Atributo | Tipo Django | Restricción | Justificación |
|---|---|---|---|
| id | BigAutoField | PK, auto | Identificador automático |
| nombre | CharField(150) | not null | Nombre o razón social |
| correo | EmailField | unique, not null | Correo único del cliente |
| telefono | CharField(20) | blank=True | Teléfono opcional |
| activo | BooleanField | default=True | Permite desactivar sin borrar |
| creado | DateTimeField | auto_now_add | Registra la fecha de creación |

## 4. Producto

| Atributo | Tipo Django | Restricción | Justificación |
|---|---|---|---|
| id | BigAutoField | PK, auto | Identificador automático |
| nombre | CharField(200) | not null | Nombre del artículo |
| precio | DecimalField(10,2) | MinValueValidator(0) | Precio no negativo |
| stock | IntegerField | default=0, MinValue(0) | Existencias no negativas |
| categoria | ForeignKey(Categoria) | PROTECT | Conserva la integridad de categorías |
| proveedor | ForeignKey(Proveedor) | SET_NULL, null=True | Permite no tener proveedor asignado |
| activo | BooleanField | default=True | Permite desactivar el producto |
| creado | DateTimeField | auto_now_add | Registra la fecha de creación |

## 5. Venta

| Atributo | Tipo Django | Restricción | Justificación |
|---|---|---|---|
| id | BigAutoField | PK, auto | Identificador automático |
| cliente | ForeignKey(Cliente) | PROTECT | Conserva el historial del cliente |
| fecha | DateTimeField | auto_now_add | Registra la fecha de creación |
| total | Propiedad calculada | No es campo de BD | Se calcula sumando los subtotales |

## 6. DetalleVenta

| Atributo | Tipo Django | Restricción | Justificación |
|---|---|---|---|
| id | BigAutoField | PK, auto | Identificador automático |
| venta | ForeignKey(Venta) | CASCADE | El detalle depende de su venta |
| producto | ForeignKey(Producto) | PROTECT | Conserva referencias históricas |
| cantidad | PositiveIntegerField | >= 1 | Registra unidades vendidas |
| precio_unitario | DecimalField(10,2) | not null | Conserva el precio al vender |

## 7. Pedido

| Atributo | Tipo Django | Restricción | Justificación |
|---|---|---|---|
| id | BigAutoField | PK, auto | Identificador automático |
| numero_pedido | CharField(20) | unique | Código único del pedido |
| cliente | ForeignKey(Cliente) | PROTECT | Todo pedido tiene un cliente |
| estado | CharField(20) | choices | Estado del pedido |
| fecha_pedido | DateTimeField | auto_now_add | Registra su creación |
| fecha_entrega | DateField | null=True | Fecha de entrega opcional |
| total_pagado | DecimalField(10,2) | null=True | Importe registrado al pagar |

Nota: Pedido se implementará en la Espiral 5.

## 8. ConfiguracionERP

| Atributo | Tipo Django | Restricción | Justificación |
|---|---|---|---|
| id | BigAutoField | PK, auto | Identificador automático |
| nombre_empresa | CharField(200) | not null | Nombre para facturas y documentos |
| rfc | CharField(13) | blank=True | RFC opcional del negocio |
| moneda | CharField(3) | default='MXN' | Moneda del sistema |
| iva_porcentaje | DecimalField(5,2) | default=16.00 | Porcentaje de IVA configurado |
| logo | ImageField | null=True, blank=True | Logo opcional de la empresa |

Nota: ConfiguracionERP se diseña como una configuración
única para todo el sistema.

## Resumen

Total de entidades: 8.

1. Categoria
2. Proveedor
3. Cliente
4. Producto
5. Venta
6. DetalleVenta
7. Pedido
8. ConfiguracionERP

Este documento servirá como referencia para implementar
los modelos Django en W05.
