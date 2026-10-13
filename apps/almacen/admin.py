from django.contrib import admin
from .models import (
    AreaAlmacen, Categoria, UnidadMedida, EstadoFisico,
    Departamento, CentroCosto, Proveedor,
    Producto, MovimientoStock, DetalleMovimiento,
    AlertaStock, SolicitudReposicion, DetalleSolicitudReposicion,
    SolicitudCompra, DetalleSolicitudCompra,
    Transferencia, DetalleTransferencia,
    Notificacion,
)


# ============================================================
# Catálogos base
# ============================================================

@admin.register(AreaAlmacen)
class AreaAlmacenAdmin(admin.ModelAdmin):
    list_display  = ("codigo", "nombre", "activa")
    search_fields = ("codigo", "nombre")
    list_filter   = ("activa",)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display  = ("nombre", "tipo", "activa")
    list_filter   = ("tipo", "activa")
    search_fields = ("nombre",)


@admin.register(UnidadMedida)
class UnidadMedidaAdmin(admin.ModelAdmin):
    list_display  = ("codigo", "nombre", "activa")
    search_fields = ("codigo", "nombre")


@admin.register(EstadoFisico)
class EstadoFisicoAdmin(admin.ModelAdmin):
    list_display  = ("nombre", "activo")


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display  = ("codigo", "nombre", "activo")
    search_fields = ("codigo", "nombre")


@admin.register(CentroCosto)
class CentroCostoAdmin(admin.ModelAdmin):
    list_display  = ("codigo", "nombre", "activo")
    search_fields = ("codigo", "nombre")


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display  = ("rif", "nombre", "telefono", "email", "activo")
    search_fields = ("rif", "nombre", "email")
    list_filter   = ("activo",)


# ============================================================
# Producto
# ============================================================

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display    = ("sku", "nombre", "area", "categoria",
                       "stock_actual", "stock_minimo", "activo")
    search_fields   = ("sku", "nombre", "codigo_qr", "numero_serie")
    list_filter     = ("area", "categoria", "estado_fisico", "activo")
    readonly_fields = ("codigo_qr", "creado_en", "actualizado_en")


# ============================================================
# Movimientos de stock
# ============================================================

class DetalleMovimientoInline(admin.TabularInline):
    model  = DetalleMovimiento
    extra  = 1
    fields = ("producto", "cantidad", "precio_unitario", "observacion")


@admin.register(MovimientoStock)
class MovimientoStockAdmin(admin.ModelAdmin):
    list_display    = ("numero", "tipo", "estado", "area",
                       "fecha_movimiento", "creado_por")
    list_filter     = ("tipo", "estado", "area")
    search_fields   = ("numero", "motivo", "observacion")
    readonly_fields = ("numero", "creado_en", "actualizado_en", "confirmado_por")
    inlines         = [DetalleMovimientoInline]


@admin.register(DetalleMovimiento)
class DetalleMovimientoAdmin(admin.ModelAdmin):
    list_display  = ("movimiento", "producto", "cantidad", "precio_unitario")
    search_fields = ("movimiento__numero", "producto__sku", "producto__nombre")


# ============================================================
# Alertas de stock
# ============================================================

@admin.register(AlertaStock)
class AlertaStockAdmin(admin.ModelAdmin):
    list_display  = ("producto", "tipo", "estado",
                     "stock_al_generar", "umbral", "creado_en")
    list_filter   = ("tipo", "estado")
    search_fields = ("producto__sku", "producto__nombre")


# ============================================================
# Solicitudes de reposición
# ============================================================

class DetalleSolicitudReposicionInline(admin.TabularInline):
    model  = DetalleSolicitudReposicion
    extra  = 1
    fields = ("producto", "cantidad", "observacion")


@admin.register(SolicitudReposicion)
class SolicitudReposicionAdmin(admin.ModelAdmin):
    list_display    = ("numero", "origen", "estado", "creado_en")
    list_filter     = ("origen", "estado")
    search_fields   = ("numero", "observacion")
    readonly_fields = ("numero", "creado_en", "actualizado_en")
    inlines         = [DetalleSolicitudReposicionInline]


@admin.register(DetalleSolicitudReposicion)
class DetalleSolicitudReposicionAdmin(admin.ModelAdmin):
    list_display  = ("solicitud", "producto", "cantidad")
    search_fields = ("solicitud__numero", "producto__sku", "producto__nombre")


# ============================================================
# Solicitudes de compra
# ============================================================

class DetalleSolicitudCompraInline(admin.TabularInline):
    model  = DetalleSolicitudCompra
    extra  = 1
    fields = ("producto", "cantidad", "precio_estimado", "observacion")


@admin.register(SolicitudCompra)
class SolicitudCompraAdmin(admin.ModelAdmin):
    list_display    = ("numero", "area_solicitante", "proveedor",
                       "estado", "fecha_solicitud", "creado_por")
    list_filter     = ("estado", "area_solicitante", "proveedor")
    search_fields   = ("numero", "motivo", "observacion")
    readonly_fields = ("numero", "creado_en", "actualizado_en",
                       "aprobado_por", "fecha_aprobacion", "movimiento_generado")
    inlines         = [DetalleSolicitudCompraInline]


@admin.register(DetalleSolicitudCompra)
class DetalleSolicitudCompraAdmin(admin.ModelAdmin):
    list_display  = ("solicitud", "producto", "cantidad", "precio_estimado")
    search_fields = ("solicitud__numero", "producto__sku", "producto__nombre")


# ============================================================
# Transferencias
# ============================================================

class DetalleTransferenciaInline(admin.TabularInline):
    """Inline para agregar los productos a mover dentro de la transferencia."""
    model               = DetalleTransferencia
    extra               = 1
    fields              = ("producto", "observacion")
    autocomplete_fields = ("producto",)
    verbose_name        = "Producto a transferir"
    verbose_name_plural = "Productos a transferir"


@admin.register(Transferencia)
class TransferenciaAdmin(admin.ModelAdmin):
    list_display        = ("numero", "area_origen", "area_destino",
                           "estado", "fecha_transferencia", "creado_por")
    list_filter         = ("estado", "area_origen", "area_destino")
    search_fields       = ("numero", "motivo", "observacion")
    readonly_fields     = ("numero", "creado_en", "actualizado_en",
                           "confirmado_por", "fecha_confirmacion", "movimiento_generado")
    autocomplete_fields = ("area_origen", "area_destino",
                           "creado_por", "confirmado_por")
    inlines             = [DetalleTransferenciaInline]
    date_hierarchy      = "fecha_transferencia"


@admin.register(DetalleTransferencia)
class DetalleTransferenciaAdmin(admin.ModelAdmin):
    """Vista global de detalles de transferencia (búsqueda y filtros)."""
    list_display        = ("transferencia", "producto", "observacion")
    list_filter         = ("transferencia__estado",
                           "transferencia__area_origen",
                           "transferencia__area_destino")
    search_fields       = ("transferencia__numero",
                           "producto__sku",
                           "producto__nombre")
    autocomplete_fields = ("transferencia", "producto")
    list_select_related = ("transferencia", "producto")
    ordering            = ("-transferencia__fecha_transferencia",)


# ============================================================
# Notificaciones
# ============================================================

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display    = ("titulo", "tipo", "usuario", "leida", "creado_en")
    list_filter     = ("tipo", "leida")
    search_fields   = ("titulo", "mensaje", "usuario__username")
    readonly_fields = ("creado_en", "actualizado_en", "leida_en")
    date_hierarchy  = "creado_en"