# Decisiones de Diseño — ERP Django

## Espiral 2 · Modelo Entidad-Relación

### D-01: Producto → Categoria usa on_delete=PROTECT

**Decisión:** No permitir borrar una categoría si tiene productos asociados.

**Alternativas consideradas:**
- `CASCADE`: borraría todos los productos de esa categoría.
- `SET_NULL`: dejaría productos sin categoría.

**Consecuencia:** Para borrar una categoría, primero se deben reasignar sus productos.

---

### D-02: Producto → Proveedor usa on_delete=SET_NULL, null=True

**Decisión:** Un producto puede existir sin proveedor asignado.

**Justificación:** Puede tratarse de un producto fabricado internamente o de un proveedor desconocido. Si se elimina un proveedor, los productos permanecen registrados.

---

### D-03: Venta → Cliente usa on_delete=PROTECT

**Decisión:** No permitir borrar un cliente que tenga historial de ventas.

**Justificación:** El historial de ventas debe conservarse. Para dar de baja a un cliente se utilizará un campo `activo=False`, en lugar de eliminar sus datos.

---

### D-04: Venta.total es una propiedad calculada

**Decisión:** El total de la venta se calcula a partir de sus detalles y no se almacena como campo de la base de datos.

**Justificación:** El total depende de los detalles de la venta. Calcularlo evita guardar un valor duplicado que podría quedar desactualizado.

---

### D-05: DetalleVenta → Producto usa on_delete=PROTECT

**Decisión:** No permitir borrar un producto que tenga ventas históricas asociadas.

**Justificación:** Los reportes históricos necesitan conservar la referencia al producto. Para descontinuarlo se utilizará `activo=False`.

---

### D-06: DetalleVenta.precio_unitario es un campo almacenado

**Decisión:** Guardar el precio del producto en el momento de la venta.

**Justificación:** El precio actual del producto puede cambiar. El detalle de la venta debe conservar el precio que se cobró originalmente.

---

### D-07: ConfiguracionERP como singleton

**Decisión:** La configuración general del ERP tendrá una sola fila de configuración.

**Implementación futura:** Se controlará en el modelo para evitar múltiples registros de configuración global.