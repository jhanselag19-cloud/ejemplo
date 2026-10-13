"""
Modelos del Módulo de Almacén.

Diseño normalizado (3FN):
- Catálogos: AreaAlmacen, Categoria, UnidadMedida, EstadoFisico, Departamento,
             CentroCosto, Proveedor, Producto.
- Transacciones: MovimientoStock, DetalleMovimiento, AlertaStock, Transferencia, Notificacion.
- Trazabilidad: usuario + timestamps en todo movimiento.

Convenciones:
- Todo monto monetario usa DecimalField.
- Todo stock se expresa en la unidad de medida del producto.
- El código QR se genera a partir de un UUID único por producto.
"""

import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q, Sum
from django.utils import timezone


# =============================================================================
# CATÁLOGOS BASE
# =============================================================================

class TimestampedModel(models.Model):
    """Base abstracta con auditoría básica."""
    creado_en     = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AreaAlmacen(TimestampedModel):
    """Áreas físicas de almacenaje."""
    codigo      = models.CharField(
        max_length=20, unique=True,
        help_text="Código único del área (ej: 02564245G1). Puede quedar 'S/C' provisionalmente."
    )
    nombre      = models.CharField(max_length=150, unique=True)
    descripcion = models.TextField(blank=True)
    activa      = models.BooleanField(default=True)

    class Meta:
        verbose_name        = "Área de almacenaje"
        verbose_name_plural = "Áreas de almacenaje"
        ordering            = ["nombre"]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Categoria(TimestampedModel):
    """Categoría lógica del producto."""
    TIPOS = [
        ("insumo",     "Insumo"),
        ("herramienta","Herramienta"),
        ("equipo",     "Equipo"),
        ("material",   "Material"),
    ]
    nombre = models.CharField(max_length=100, unique=True)
    tipo   = models.CharField(max_length=20, choices=TIPOS, default="insumo")
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name        = "Categoría"
        verbose_name_plural = "Categorías"
        ordering            = ["nombre"]

    def __str__(self):
        return self.nombre


class UnidadMedida(TimestampedModel):
    """Unidad de medida."""
    codigo   = models.CharField(max_length=10, unique=True)
    nombre   = models.CharField(max_length=50, unique=True)
    activa   = models.BooleanField(default=True)

    class Meta:
        verbose_name        = "Unidad de medida"
        verbose_name_plural = "Unidades de medida"
        ordering            = ["nombre"]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class EstadoFisico(TimestampedModel):
    """Condición física del ítem."""
    nombre = models.CharField(max_length=50, unique=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name        = "Estado físico"
        verbose_name_plural = "Estados físicos"
        ordering            = ["nombre"]

    def __str__(self):
        return self.nombre


class Departamento(TimestampedModel):
    """Departamento o centro de costo."""
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=150, unique=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name        = "Departamento"
        verbose_name_plural = "Departamentos"
        ordering            = ["nombre"]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class CentroCosto(TimestampedModel):
    """Centro de costo contable."""
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=150, unique=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name        = "Centro de costo"
        verbose_name_plural = "Centros de costo"
        ordering            = ["nombre"]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Proveedor(TimestampedModel):
    """Proveedor de mercancía."""
    rif       = models.CharField(
        max_length=20, unique=True,
        validators=[RegexValidator(r"^[JGVEC]-\d{8,9}-?\\d?$", "RIF inválido (ej: J-12345678-9)")]
    )
    nombre    = models.CharField(max_length=200)
    telefono  = models.CharField(max_length=30, blank=True)
    email     = models.EmailField(blank=True)
    direccion = models.TextField(blank=True)
    activo    = models.BooleanField(default=True)

    class Meta:
        verbose_name        = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering            = ["nombre"]

    def __str__(self):
        return self.nombre


# =============================================================================
# PRODUCTO
# =============================================================================

class Producto(TimestampedModel):
    """Ítem del catálogo."""
    sku             = models.CharField(max_length=40, unique=True)
    codigo_qr       = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    codigo_barras   = models.CharField(max_length=80, blank=True, null=True, unique=True)

    nombre          = models.CharField(max_length=200)
    descripcion     = models.TextField(blank=True)
    numero_serie    = models.CharField(max_length=80, blank=True, null=True)

    area            = models.ForeignKey(AreaAlmacen, on_delete=models.PROTECT, related_name="productos")
    categoria       = models.ForeignKey(Categoria,   on_delete=models.PROTECT, related_name="productos")
    unidad_medida   = models.ForeignKey(UnidadMedida,on_delete=models.PROTECT, related_name="productos")
    estado_fisico   = models.ForeignKey(EstadoFisico,on_delete=models.PROTECT, related_name="productos")
    proveedor       = models.ForeignKey(
        Proveedor, on_delete=models.SET_NULL, null=True, blank=True, related_name="productos"
    )

    # ✅ Precio con decimales (monto monetario)
    precio_unitario = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )

    # ✅ Stock como enteros (sin decimales)
    stock_actual    = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    stock_minimo    = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )

    # ✅ NUEVO: Umbral a partir del cual se generan alertas
    umbral_alerta   = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Stock a partir del cual se genera una alerta. Si es 0, se usa el stock mínimo + 10%."
    )

    activo          = models.BooleanField(default=True)

    class Meta:
        verbose_name        = "Producto"
        verbose_name_plural = "Productos"
        ordering            = ["nombre"]
        indexes             = [
            models.Index(fields=["sku"]),
            models.Index(fields=["nombre"]),
            models.Index(fields=["area", "categoria"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(stock_actual__gte=0),
                name="producto_stock_actual_no_negativo",
            ),
            models.CheckConstraint(
                check=Q(stock_minimo__gte=0),
                name="producto_stock_minimo_no_negativo",
            ),
            models.CheckConstraint(
                check=Q(umbral_alerta__gte=0),
                name="producto_umbral_alerta_no_negativo",
            ),
        ]

    def __str__(self):
        return f"{self.sku} - {self.nombre}"

    @property
    def valor_inventario(self) -> Decimal:
        return Decimal(self.stock_actual or 0) * (self.precio_unitario or Decimal("0"))

    @property
    def umbral_efectivo(self) -> int:
        """Devuelve el umbral real de alerta.
        Si `umbral_alerta` es 0, se calcula como stock_minimo + 10%.
        """
        if self.umbral_alerta and self.umbral_alerta > 0:
            return self.umbral_alerta
        # Por defecto: stock_minimo + 10% (redondeado hacia arriba)
        return int(self.stock_minimo * 1.10)

    @property
    def bajo_minimo(self) -> bool:
        """El stock está por debajo o igual al mínimo."""
        return self.stock_actual <= self.stock_minimo

    @property
    def cerca_del_minimo(self) -> bool:
        """El stock está por encima del mínimo pero por debajo del umbral de alerta."""
        return (
            self.stock_actual > self.stock_minimo
            and self.stock_actual <= self.umbral_efectivo
        )

    @property
    def sin_stock(self) -> bool:
        """El stock está en cero."""
        return self.stock_actual <= 0

    @property
    def estado_stock(self) -> str:
        """Devuelve un string con el estado del stock:
        'sin_stock', 'bajo_minimo', 'cerca_minimo' o 'ok'.
        """
        if self.sin_stock:
            return "sin_stock"
        if self.bajo_minimo:
            return "bajo_minimo"
        if self.cerca_del_minimo:
            return "cerca_minimo"
        return "ok"

    def recalcular_stock(self, guardar: bool = True) -> int:
        total = self.detalles_movimiento.filter(
            movimiento__estado=MovimientoStock.ESTADO_CONFIRMADO
        ).aggregate(total=Sum("cantidad_firmada"))["total"] or 0

        self.stock_actual = int(total)
        if guardar:
            self.save(update_fields=["stock_actual", "actualizado_en"])
        return self.stock_actual


# =============================================================================
# MOVIMIENTOS DE STOCK
# =============================================================================

class MovimientoStock(TimestampedModel):
    """Cabecera del movimiento."""
    TIPO_ENTRADA_COMPRA       = "entrada_compra"
    TIPO_ENTRADA_TRANSFERENCIA= "entrada_transferencia"
    TIPO_ENTRADA_DEVOLUCION   = "entrada_devolucion"
    TIPO_SALIDA_DESPACHO      = "salida_despacho"
    TIPO_SALIDA_CONSUMO       = "salida_consumo"
    TIPO_AJUSTE_POSITIVO      = "ajuste_positivo"
    TIPO_AJUSTE_NEGATIVO      = "ajuste_negativo"

    TIPOS = [
        (TIPO_ENTRADA_COMPRA,        "Entrada por compra"),
        (TIPO_ENTRADA_TRANSFERENCIA, "Entrada por transferencia"),
        (TIPO_ENTRADA_DEVOLUCION,    "Entrada por devolución"),
        (TIPO_SALIDA_DESPACHO,       "Salida por despacho"),
        (TIPO_SALIDA_CONSUMO,        "Salida por consumo"),
        (TIPO_AJUSTE_POSITIVO,       "Ajuste positivo (auditoría)"),
        (TIPO_AJUSTE_NEGATIVO,       "Ajuste negativo (auditoría)"),
    ]

    ESTADO_BORRADOR   = "borrador"
    ESTADO_CONFIRMADO = "confirmado"
    ESTADO_ANULADO    = "anulado"

    ESTADOS = [
        (ESTADO_BORRADOR,   "Borrador"),
        (ESTADO_CONFIRMADO, "Confirmado"),
        (ESTADO_ANULADO,    "Anulado"),
    ]

    numero       = models.CharField(max_length=30, unique=True, blank=True)
    tipo         = models.CharField(max_length=30, choices=TIPOS)
    estado       = models.CharField(max_length=15, choices=ESTADOS, default=ESTADO_BORRADOR)

    area         = models.ForeignKey(
        AreaAlmacen, on_delete=models.PROTECT, related_name="movimientos"
    )
    proveedor    = models.ForeignKey(
        Proveedor, on_delete=models.SET_NULL, null=True, blank=True, related_name="movimientos"
    )
    departamento = models.ForeignKey(
        Departamento, on_delete=models.SET_NULL, null=True, blank=True, related_name="movimientos"
    )
    centro_costo = models.ForeignKey(
        CentroCosto, on_delete=models.SET_NULL, null=True, blank=True, related_name="movimientos"
    )

    creado_por   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="movimientos_creados"
    )
    confirmado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="movimientos_confirmados"
    )
    fecha_movimiento = models.DateTimeField(default=timezone.now)

    motivo       = models.CharField(max_length=200, blank=True)
    observacion  = models.TextField(blank=True)

    class Meta:
        verbose_name        = "Movimiento de stock"
        verbose_name_plural = "Movimientos de stock"
        ordering            = ["-fecha_movimiento", "-id"]
        indexes             = [
            models.Index(fields=["tipo", "estado"]),
            models.Index(fields=["fecha_movimiento"]),
            models.Index(fields=["area"]),
        ]

    def __str__(self):
        return f"{self.numero or '(borrador)'} - {self.get_tipo_display()}"

    def save(self, *args, **kwargs):
        if not self.numero:
            prefijo = {
                self.TIPO_ENTRADA_COMPRA:        "EC",
                self.TIPO_ENTRADA_TRANSFERENCIA: "ET",
                self.TIPO_ENTRADA_DEVOLUCION:    "ED",
                self.TIPO_SALIDA_DESPACHO:       "SD",
                self.TIPO_SALIDA_CONSUMO:        "SC",
                self.TIPO_AJUSTE_POSITIVO:       "AP",
                self.TIPO_AJUSTE_NEGATIVO:       "AN",
            }.get(self.tipo, "MV")

            ultimo = MovimientoStock.objects.filter(numero__startswith=prefijo).order_by("-id").first()
            secuencia = 1
            if ultimo and ultimo.numero:
                try:
                    secuencia = int(ultimo.numero.split("-")[-1]) + 1
                except (ValueError, IndexError):
                    secuencia = 1
            self.numero = f"{prefijo}-{secuencia:06d}"
        super().save(*args, **kwargs)

    def confirmar(self, usuario):
        if self.estado != self.ESTADO_BORRADOR:
            raise ValueError("Solo se pueden confirmar movimientos en borrador.")

        for detalle in self.detalles.select_related("producto"):
            detalle.aplicar_stock()

        self.estado          = self.ESTADO_CONFIRMADO
        self.confirmado_por  = usuario
        self.save(update_fields=["estado", "confirmado_por", "actualizado_en"])

    def anular(self, usuario):
        if self.estado == self.ESTADO_CONFIRMADO:
            for detalle in self.detalles.select_related("producto"):
                detalle.revertir_stock()
        self.estado = self.ESTADO_ANULADO
        self.save(update_fields=["estado", "actualizado_en"])


class DetalleMovimiento(TimestampedModel):
    """Línea de un movimiento."""
    movimiento      = models.ForeignKey(
        MovimientoStock, on_delete=models.CASCADE, related_name="detalles"
    )
    producto        = models.ForeignKey(
        Producto,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="detalles_movimiento",
    )
    cantidad        = models.DecimalField(
        max_digits=14, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))]
    )
    precio_unitario = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00"),
        help_text="Precio al momento del movimiento (histórico)."
    )
    observacion     = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name        = "Detalle de movimiento"
        verbose_name_plural = "Detalles de movimiento"
        constraints = [
            models.CheckConstraint(
                check=Q(cantidad__gt=0),
                name="detalle_cantidad_positiva",
            ),
        ]

    def __str__(self):
        sku = self.producto.sku if self.producto else "(producto eliminado)"
        return f"{sku} x {self.cantidad}"

    @property
    def es_entrada(self) -> bool:
        return self.movimiento.tipo in (
            MovimientoStock.TIPO_ENTRADA_COMPRA,
            MovimientoStock.TIPO_ENTRADA_TRANSFERENCIA,
            MovimientoStock.TIPO_ENTRADA_DEVOLUCION,
            MovimientoStock.TIPO_AJUSTE_POSITIVO,
        )

    @property
    def cantidad_firmada(self) -> Decimal:
        return self.cantidad if self.es_entrada else -self.cantidad

    @property
    def subtotal(self) -> Decimal:
        return self.cantidad * self.precio_unitario

    def aplicar_stock(self):
        if not self.producto:
            return
        self.producto.stock_actual = (
            self.producto.stock_actual + int(self.cantidad_firmada)
        )
        self.producto.save(update_fields=["stock_actual", "actualizado_en"])

    def revertir_stock(self):
        if not self.producto:
            return
        self.producto.stock_actual = (
            self.producto.stock_actual - int(self.cantidad_firmada)
        )
        self.producto.save(update_fields=["stock_actual", "actualizado_en"])


# =============================================================================
# ALERTAS Y COMPRAS AUTOMÁTICAS
# =============================================================================

class AlertaStock(TimestampedModel):
    """Alerta generada por stock mínimo o inexistencia."""
    TIPO_MINIMO     = "minimo"
    TIPO_INEXISTENCIA = "inexistencia"
    TIPO_CERCA_MINIMO = "cerca_minimo"   # ✅ NUEVO: alerta preventiva

    TIPOS = [
        (TIPO_MINIMO,       "Stock por debajo del mínimo"),
        (TIPO_INEXISTENCIA, "Stock en cero (inexistencia)"),
        (TIPO_CERCA_MINIMO, "Stock cerca del mínimo"),
    ]

    ESTADO_PENDIENTE  = "pendiente"
    ESTADO_ATENDIDA   = "atendida"
    ESTADO_DESCARTADA = "descartada"

    ESTADOS = [
        (ESTADO_PENDIENTE,  "Pendiente"),
        (ESTADO_ATENDIDA,   "Atendida"),
        (ESTADO_DESCARTADA, "Descartada"),
    ]

    producto        = models.ForeignKey(
        Producto,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="alertas",
    )
    tipo            = models.CharField(max_length=20, choices=TIPOS)
    estado          = models.CharField(max_length=15, choices=ESTADOS, default=ESTADO_PENDIENTE)
    stock_al_generar= models.IntegerField()   # ✅ Ahora entero
    umbral          = models.IntegerField()   # ✅ Ahora entero
    mensaje         = models.CharField(max_length=255, blank=True)
    atendida_por    = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="alertas_atendidas"
    )

    class Meta:
        verbose_name        = "Alerta de stock"
        verbose_name_plural = "Alertas de stock"
        ordering            = ["-creado_en"]
        indexes             = [
            models.Index(fields=["estado", "tipo"]),
        ]

    def __str__(self):
        sku = self.producto.sku if self.producto else "(producto eliminado)"
        return f"[{self.get_tipo_display()}] {sku} ({self.stock_al_generar})"


class SolicitudReposicion(TimestampedModel):
    """Pre-orden generada automáticamente por las alertas."""
    ESTADO_BORRADOR   = "borrador"
    ESTADO_ENVIADA    = "enviada"
    ESTADO_PROCESADA  = "procesada"
    ESTADO_CANCELADA  = "cancelada"

    ESTADOS = [
        (ESTADO_BORRADOR,  "Borrador"),
        (ESTADO_ENVIADA,   "Enviada a Compras"),
        (ESTADO_PROCESADA, "Procesada"),
        (ESTADO_CANCELADA, "Cancelada"),
    ]

    ORIGEN_ALERTA_MINIMO   = "alerta_minimo"
    ORIGEN_INEXISTENCIA    = "inexistencia"

    ORIGENES = [
        (ORIGEN_ALERTA_MINIMO, "Alerta de stock mínimo"),
        (ORIGEN_INEXISTENCIA,  "Stock en cero"),
    ]

    numero        = models.CharField(max_length=30, unique=True, blank=True)
    origen        = models.CharField(max_length=20, choices=ORIGENES)
    estado        = models.CharField(max_length=15, choices=ESTADOS, default=ESTADO_BORRADOR)
    alerta        = models.ForeignKey(
        AlertaStock, on_delete=models.SET_NULL, null=True, blank=True, related_name="solicitudes"
    )
    generada_por  = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="solicitudes_generadas"
    )
    observacion   = models.TextField(blank=True)

    class Meta:
        verbose_name        = "Solicitud de reposición"
        verbose_name_plural = "Solicitudes de reposición"
        ordering            = ["-creado_en"]

    def __str__(self):
        return f"{self.numero or '(borrador)'} - {self.get_origen_display()}"


class DetalleSolicitudReposicion(TimestampedModel):
    """Línea de una solicitud de reposición."""
    solicitud    = models.ForeignKey(
        SolicitudReposicion, on_delete=models.CASCADE, related_name="detalles"
    )
    producto     = models.ForeignKey(
        Producto,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="solicitudes_reposicion",
    )
    cantidad     = models.DecimalField(
        max_digits=14, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))]
    )
    observacion  = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name        = "Detalle de solicitud"
        verbose_name_plural = "Detalles de solicitud"

    def __str__(self):
        sku = self.producto.sku if self.producto else "(producto eliminado)"
        return f"{sku} x {self.cantidad}"


# =============================================================================
# MÓDULO DE COMPRAS
# =============================================================================

class SolicitudCompra(TimestampedModel):
    """Solicitud de compra."""
    ESTADO_PENDIENTE  = "pendiente"
    ESTADO_APROBADA   = "aprobada"
    ESTADO_RECHAZADA  = "rechazada"
    ESTADO_COMPRADA   = "comprada"

    ESTADOS = [
        (ESTADO_PENDIENTE, "Pendiente"),
        (ESTADO_APROBADA,  "Aprobada"),
        (ESTADO_RECHAZADA, "Rechazada"),
        (ESTADO_COMPRADA,  "Comprada"),
    ]

    numero              = models.CharField(max_length=30, unique=True, blank=True)
    estado              = models.CharField(max_length=15, choices=ESTADOS, default=ESTADO_PENDIENTE)

    area_solicitante    = models.ForeignKey(
        AreaAlmacen, on_delete=models.PROTECT, related_name="solicitudes_compra"
    )
    departamento        = models.ForeignKey(
        Departamento, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="solicitudes_compra"
    )
    centro_costo        = models.ForeignKey(
        CentroCosto, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="solicitudes_compra"
    )
    proveedor           = models.ForeignKey(
        Proveedor, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="solicitudes_compra"
    )

    creado_por          = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="solicitudes_compra_creadas"
    )
    aprobado_por        = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="solicitudes_compra_aprobadas"
    )
    fecha_solicitud     = models.DateTimeField(default=timezone.now)
    fecha_necesaria     = models.DateField(null=True, blank=True)
    fecha_aprobacion    = models.DateTimeField(null=True, blank=True)

    movimiento_generado = models.OneToOneField(
        MovimientoStock, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="solicitud_origen"
    )

    motivo              = models.CharField(max_length=200)
    observacion         = models.TextField(blank=True)

    class Meta:
        verbose_name        = "Solicitud de compra"
        verbose_name_plural = "Solicitudes de compra"
        ordering            = ["-fecha_solicitud", "-id"]
        indexes             = [
            models.Index(fields=["estado"]),
            models.Index(fields=["fecha_solicitud"]),
        ]

    def __str__(self):
        return f"{self.numero or '(borrador)'} - {self.get_estado_display()}"

    def save(self, *args, **kwargs):
        if not self.numero:
            ultimo = SolicitudCompra.objects.filter(numero__startswith="SC").order_by("-id").first()
            secuencia = 1
            if ultimo and ultimo.numero:
                try:
                    secuencia = int(ultimo.numero.split("-")[-1]) + 1
                except (ValueError, IndexError):
                    secuencia = 1
            self.numero = f"SC-{secuencia:06d}"
        super().save(*args, **kwargs)

    def aprobar(self, usuario, proveedor=None):
        if self.estado != self.ESTADO_PENDIENTE:
            raise ValueError("Solo se pueden aprobar solicitudes pendientes.")
        self.estado = self.ESTADO_APROBADA
        self.aprobado_por = usuario
        self.fecha_aprobacion = timezone.now()
        if proveedor:
            self.proveedor = proveedor
        self.save(update_fields=["estado", "aprobado_por", "fecha_aprobacion", "proveedor", "actualizado_en"])

    def rechazar(self, usuario, motivo_rechazo=""):
        if self.estado != self.ESTADO_PENDIENTE:
            raise ValueError("Solo se pueden rechazar solicitudes pendientes.")
        self.estado = self.ESTADO_RECHAZADA
        self.aprobado_por = usuario
        if motivo_rechazo:
            self.observacion = (self.observacion + "\n" + motivo_rechazo).strip()
        self.save(update_fields=["estado", "aprobado_por", "observacion", "actualizado_en"])

    def marcar_comprada(self, usuario):
        if self.estado != self.ESTADO_APROBADA:
            raise ValueError("Solo se pueden marcar como compradas las solicitudes aprobadas.")
        if self.movimiento_generado:
            raise ValueError("Esta solicitud ya tiene un movimiento asociado.")
        if not self.detalles.exists():
            raise ValueError("No se puede marcar como comprada una solicitud sin detalles.")

        movimiento = MovimientoStock.objects.create(
            tipo=MovimientoStock.TIPO_ENTRADA_COMPRA,
            estado=MovimientoStock.ESTADO_CONFIRMADO,
            area=self.area_solicitante,
            proveedor=self.proveedor,
            departamento=self.departamento,
            centro_costo=self.centro_costo,
            creado_por=self.creado_por,
            confirmado_por=usuario,
            motivo=f"Compra según solicitud {self.numero}",
        )

        for detalle in self.detalles.select_related("producto"):
            if not detalle.producto:
                continue
            DetalleMovimiento.objects.create(
                movimiento=movimiento,
                producto=detalle.producto,
                cantidad=detalle.cantidad,
                precio_unitario=detalle.precio_estimado or detalle.producto.precio_unitario or 0,
            )
            detalle.producto.stock_actual += int(detalle.cantidad)
            detalle.producto.save(update_fields=["stock_actual", "actualizado_en"])

        self.estado = self.ESTADO_COMPRADA
        self.movimiento_generado = movimiento
        self.save(update_fields=["estado", "movimiento_generado", "actualizado_en"])


class DetalleSolicitudCompra(TimestampedModel):
    """Línea de una solicitud de compra."""
    solicitud       = models.ForeignKey(
        SolicitudCompra, on_delete=models.CASCADE, related_name="detalles"
    )
    producto        = models.ForeignKey(
        Producto,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="detalles_solicitud_compra",
    )
    cantidad        = models.DecimalField(
        max_digits=14, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))]
    )
    precio_estimado = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00"),
        help_text="Precio estimado al momento de la solicitud."
    )
    observacion     = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name        = "Detalle de solicitud de compra"
        verbose_name_plural = "Detalles de solicitud de compra"

    def __str__(self):
        sku = self.producto.sku if self.producto else "(producto eliminado)"
        return f"{sku} x {self.cantidad}"

    @property
    def subtotal(self):
        return self.cantidad * self.precio_estimado


# =============================================================================
# MÓDULO DE TRANSFERENCIAS
# =============================================================================

class Transferencia(TimestampedModel):
    """
    Transferencia de productos entre áreas de almacén.
    Al confirmar, los productos cambian su `area` al destino y se registra
    un movimiento de trazabilidad.
    """
    ESTADO_BORRADOR   = "borrador"
    ESTADO_CONFIRMADA = "confirmada"
    ESTADO_ANULADA    = "anulada"

    ESTADOS = [
        (ESTADO_BORRADOR,   "Borrador"),
        (ESTADO_CONFIRMADA, "Confirmada"),
        (ESTADO_ANULADA,    "Anulada"),
    ]

    numero              = models.CharField(max_length=30, unique=True, blank=True)
    estado              = models.CharField(max_length=15, choices=ESTADOS, default=ESTADO_BORRADOR)

    area_origen         = models.ForeignKey(
        AreaAlmacen, on_delete=models.PROTECT,
        related_name="transferencias_salientes",
        help_text="Área desde la que salen los productos."
    )
    area_destino        = models.ForeignKey(
        AreaAlmacen, on_delete=models.PROTECT,
        related_name="transferencias_entrantes",
        help_text="Área a la que llegan los productos."
    )

    creado_por          = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="transferencias_creadas"
    )
    confirmado_por      = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="transferencias_confirmadas"
    )
    fecha_transferencia = models.DateTimeField(default=timezone.now)
    fecha_confirmacion  = models.DateTimeField(null=True, blank=True)

    movimiento_generado = models.OneToOneField(
        MovimientoStock, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="transferencia_origen",
        help_text="Movimiento generado al confirmar la transferencia."
    )

    motivo              = models.CharField(max_length=200)
    observacion         = models.TextField(blank=True)

    class Meta:
        verbose_name        = "Transferencia"
        verbose_name_plural = "Transferencias"
        ordering            = ["-fecha_transferencia", "-id"]
        indexes             = [
            models.Index(fields=["estado"]),
            models.Index(fields=["fecha_transferencia"]),
        ]

    def __str__(self):
        return f"{self.numero or '(borrador)'} - {self.area_origen.nombre} → {self.area_destino.nombre}"

    def save(self, *args, **kwargs):
        if not self.numero:
            ultimo = Transferencia.objects.filter(numero__startswith="TR").order_by("-id").first()
            secuencia = 1
            if ultimo and ultimo.numero:
                try:
                    secuencia = int(ultimo.numero.split("-")[-1]) + 1
                except (ValueError, IndexError):
                    secuencia = 1
            self.numero = f"TR-{secuencia:06d}"
        super().save(*args, **kwargs)

    def confirmar(self, usuario):
        if self.estado != self.ESTADO_BORRADOR:
            raise ValueError("Solo se pueden confirmar transferencias en borrador.")

        if self.area_origen == self.area_destino:
            raise ValueError("El área de origen y destino no pueden ser la misma.")

        if not self.detalles.exists():
            raise ValueError("No se puede confirmar una transferencia sin productos.")

        for detalle in self.detalles.select_related("producto"):
            if not detalle.producto:
                raise ValueError("La transferencia contiene un producto eliminado.")
            if detalle.producto.area != self.area_origen:
                raise ValueError(
                    f"El producto {detalle.producto.sku} no pertenece al área de origen."
                )

        movimiento = MovimientoStock.objects.create(
            tipo=MovimientoStock.TIPO_ENTRADA_TRANSFERENCIA,
            estado=MovimientoStock.ESTADO_CONFIRMADO,
            area=self.area_destino,
            creado_por=self.creado_por,
            confirmado_por=usuario,
            motivo=f"Transferencia {self.numero} desde {self.area_origen.nombre}",
            observacion=self.observacion,
        )

        for detalle in self.detalles.select_related("producto"):
            producto = detalle.producto
            if not producto:
                continue

            DetalleMovimiento.objects.create(
                movimiento=movimiento,
                producto=producto,
                cantidad=producto.stock_actual or 1,
                precio_unitario=producto.precio_unitario or 0,
                observacion=f"Movido de {self.area_origen.nombre} a {self.area_destino.nombre}",
            )

            producto.area = self.area_destino
            producto.save(update_fields=["area", "actualizado_en"])

        self.estado = self.ESTADO_CONFIRMADA
        self.confirmado_por = usuario
        self.fecha_confirmacion = timezone.now()
        self.movimiento_generado = movimiento
        self.save(update_fields=[
            "estado", "confirmado_por", "fecha_confirmacion",
            "movimiento_generado", "actualizado_en"
        ])

    def anular(self, usuario):
        if self.estado != self.ESTADO_BORRADOR:
            raise ValueError("Solo se pueden anular transferencias en borrador.")
        self.estado = self.ESTADO_ANULADA
        self.confirmado_por = usuario
        self.save(update_fields=["estado", "confirmado_por", "actualizado_en"])


class DetalleTransferencia(TimestampedModel):
    """Línea de una transferencia: un producto que se mueve de área."""
    transferencia = models.ForeignKey(
        Transferencia, on_delete=models.CASCADE, related_name="detalles"
    )
    producto      = models.ForeignKey(
        Producto,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="transferencias",
    )
    observacion   = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name        = "Detalle de transferencia"
        verbose_name_plural = "Detalles de transferencia"

    def __str__(self):
        if self.producto:
            return f"{self.producto.sku} ({self.producto.area.nombre})"
        return "(producto eliminado)"


# =============================================================================
# MÓDULO DE NOTIFICACIONES
# =============================================================================

class Notificacion(TimestampedModel):
    """
    Notificación para el usuario. Se genera automáticamente al crear
    una solicitud de compra, transferencia u otras acciones que requieran atención.
    """
    TIPO_SOLICITUD_COMPRA = "solicitud_compra"
    TIPO_STOCK_BAJO       = "stock_bajo"
    TIPO_TRANSFERENCIA    = "transferencia"
    TIPO_INFO             = "info"

    TIPOS = [
        (TIPO_SOLICITUD_COMPRA, "Nueva solicitud de compra"),
        (TIPO_STOCK_BAJO,       "Stock bajo"),
        (TIPO_TRANSFERENCIA,    "Nueva transferencia"),
        (TIPO_INFO,             "Información"),
    ]

    titulo      = models.CharField(max_length=200)
    mensaje     = models.TextField(blank=True)
    tipo        = models.CharField(max_length=30, choices=TIPOS, default=TIPO_INFO)

    usuario     = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        null=True, blank=True, related_name="notificaciones",
        help_text="Si es nulo, se considera una notificación global."
    )

    url         = models.CharField(max_length=300, blank=True, help_text="URL a la que lleva al hacer clic.")

    leida       = models.BooleanField(default=False)
    leida_en    = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name        = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering            = ["-creado_en"]
        indexes             = [
            models.Index(fields=["usuario", "leida"]),
            models.Index(fields=["creado_en"]),
        ]

    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.titulo}"

    def marcar_como_leida(self):
        self.leida = True
        self.leida_en = timezone.now()
        self.save(update_fields=["leida", "leida_en", "actualizado_en"])