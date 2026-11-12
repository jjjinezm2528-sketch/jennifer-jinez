
# Parte 3. Diseño de relaciones y normalización a 3FN

## 1. Objetivo

Diseñar las relaciones entre las entidades del sistema ERP y justificar la organización de los datos mediante las tres primeras formas normales (1FN, 2FN y 3FN), con el propósito de reducir la duplicidad, mantener la integridad y facilitar el mantenimiento de la base de datos.

## 2. Relaciones y cardinalidades

| Entidad principal | Entidad relacionada | Cardinalidad | Justificación |
|---|---|---|---|
| Categoria | Producto | 1:N | Una categoría puede clasificar varios productos. Cada producto pertenece a una categoría. |
| Proveedor | Producto | 1:N opcional | Un proveedor puede suministrar varios productos. Un producto puede tener un proveedor o ninguno. |
| Cliente | Venta | 1:N | Un cliente puede realizar varias ventas. Cada venta corresponde a un cliente. |
| Venta | DetalleVenta | 1:N | Una venta contiene uno o varios detalles. Cada detalle pertenece a una venta. |
| Producto | DetalleVenta | 1:N | Un producto puede aparecer en distintos detalles de venta. Cada detalle corresponde a un producto. |
| Cliente | Pedido | 1:N | Un cliente puede generar varios pedidos. Cada pedido corresponde a un cliente. |

### Interpretación de las cardinalidades

- **1:1:** una instancia de una entidad se relaciona con una sola instancia de otra.
- **1:N:** una instancia de una entidad puede relacionarse con varias instancias de otra.
- **N:M:** varias instancias de una entidad pueden relacionarse con varias de otra. En una base de datos relacional, normalmente se representa mediante una entidad intermedia.

En este diseño, la relación entre Venta y Producto es conceptualmente N:M, porque una venta puede incluir varios productos y un producto puede aparecer en varias ventas. Se resuelve mediante la entidad intermedia DetalleVenta.

## 3. Primera forma normal (1FN)

Una tabla cumple la primera forma normal cuando cada atributo almacena valores individuales y no existen grupos repetidos de datos en una misma columna.

En el ERP, los datos se distribuyen en entidades separadas. Por ejemplo, los datos de un producto se guardan en Producto, mientras que sus datos de clasificación se encuentran en Categoria.

Los productos de una venta no se almacenan como una lista dentro de una columna de Venta. Cada producto vendido se representa mediante un registro independiente en DetalleVenta.

**Resultado:** el diseño establece atributos individuales y utiliza registros separados para representar los detalles de las ventas.

## 4. Segunda forma normal (2FN)

Una tabla cumple la segunda forma normal cuando cumple la 1FN y cada atributo que no forma parte de una clave depende de la clave primaria completa, sin depender solamente de una parte de ella.

Las entidades propuestas utilizan claves primarias individuales, como id. Por ello, no existen claves primarias compuestas que provoquen dependencias parciales en el diseño actual.

En DetalleVenta, cada registro tiene su propio identificador. Además, la cantidad y el precio_unitario corresponden al detalle específico de una venta.

**Resultado:** no se identifican dependencias parciales en el diseño propuesto. La revisión definitiva deberá mantenerse cuando se implementen los modelos y sus restricciones.

## 5. Tercera forma normal (3FN)

Una tabla cumple la tercera forma normal cuando cumple la 2FN y sus atributos que no son clave dependen de la clave primaria, no de otros atributos que tampoco son clave.

Para favorecer esta condición, los datos se organizan de la siguiente manera:

- Categoria almacena los datos propios de las categorías.
- Proveedor almacena los datos de los proveedores.
- Cliente almacena los datos de los clientes.
- Producto almacena sus propios datos y las referencias a Categoria y Proveedor.
- Venta almacena los datos de la venta y la referencia al cliente.
- DetalleVenta almacena la cantidad y el precio unitario histórico de cada producto vendido.
- Pedido almacena los datos propios del pedido y la referencia al cliente.
- ConfiguracionERP almacena la configuración general de la empresa.

Por ejemplo, el nombre del proveedor no se repite como un campo en cada producto. Producto utiliza una clave foránea que referencia a Proveedor. De manera similar, los datos del cliente se conservan en Cliente y se referencian desde Venta y Pedido.

El total de Venta se plantea como un valor calculado a partir de los subtotales de DetalleVenta, evitando almacenar el mismo total por separado y que quede desactualizado.

**Resultado:** la separación de las entidades reduce la duplicidad de datos y evita las dependencias transitivas previstas en el diseño. La conformidad definitiva con 3FN deberá validarse al implementar los modelos.

## 6. Integridad y reglas de diseño

- Las claves primarias identifican de forma única cada registro.
- Las claves foráneas relacionan las entidades y ayudan a mantener la integridad referencial.
- Categoria se protege contra su eliminación cuando existen productos relacionados.
- Proveedor puede quedar sin referencia en un producto cuando se elimina el proveedor, según la regla SET_NULL.
- Cliente se protege contra su eliminación cuando existen ventas o pedidos relacionados.
- Producto se protege contra su eliminación cuando existen detalles de venta relacionados.
- DetalleVenta conserva el precio unitario histórico para que cambios posteriores en el precio del producto no alteren ventas anteriores.

## 7. Observaciones pendientes de validar

1. Confirmar que las cardinalidades coincidan con el diagrama ER definitivo.
2. Definir si Pedido necesitará una entidad de detalle para registrar los productos incluidos en cada pedido.
3. Confirmar que total_pagado representa el importe efectivamente pagado y no el total calculado del pedido.
4. Verificar las restricciones, claves foráneas y reglas de eliminación en los modelos Django.
5. Confirmar que ConfiguracionERP solo permita una configuración global si esa es la regla del negocio.

## 8. Conclusión

La separación de las ocho entidades permite organizar los datos del ERP de manera clara, reducir la duplicidad y establecer relaciones mediante claves foráneas. El diseño contempla las reglas principales de integridad y busca cumplir las tres primeras formas normales. La validación final se realizará al implementar los modelos, revisar las restricciones y ejecutar las pruebas correspondientes.
