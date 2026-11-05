# Diagrama Entidad-Relación — ERP Django

## Espiral 2 · Modelo de datos

```mermaid
erDiagram
    CATEGORIA {
        bigint id PK
        varchar nombre UK
        text descripcion
    }

    PROVEEDOR {
        bigint id PK
        varchar nombre
        varchar correo UK
        varchar telefono
        bool activo
    }

    CLIENTE {
        bigint id PK
        varchar nombre
        varchar correo UK
        varchar telefono
        bool activo
    }

    PRODUCTO {
        bigint id PK
        varchar nombre
        decimal precio
        int stock
        bigint categoria_id FK
        bigint proveedor_id FK
        bool activo
    }

    VENTA {
        bigint id PK
        bigint cliente_id FK
        datetime fecha
    }

    DETALLE_VENTA {
        bigint id PK
        bigint venta_id FK
        bigint producto_id FK
        int cantidad
        decimal precio_unitario
    }

    PEDIDO {
        bigint id PK
        varchar numero_pedido UK
        bigint cliente_id FK
        varchar estado
        datetime fecha_pedido
    }

    CONFIGURACION_ERP {
        bigint id PK
        varchar nombre_empresa
        varchar rfc
        varchar moneda
        decimal iva_porcentaje
    }

    CATEGORIA ||--o{ PRODUCTO : clasifica
    PROVEEDOR |o--o{ PRODUCTO : suministra
    CLIENTE ||--o{ VENTA : realiza
    CLIENTE ||--o{ PEDIDO : genera
    VENTA ||--o{ DETALLE_VENTA : contiene
    PRODUCTO ||--o{ DETALLE_VENTA : incluido_en
```

## Notas de diseño

- El total de Venta se calcula a partir de sus detalles.
- DetalleVenta conserva el precio histórico del producto.
- ConfiguracionERP está diseñada para tener una sola configuración global.
- Pedido se implementará en una etapa posterior.