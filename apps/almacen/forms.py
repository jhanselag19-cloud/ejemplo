# almacen/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import (
    Producto, AreaAlmacen, Categoria, UnidadMedida, EstadoFisico, Proveedor,
    MovimientoStock, Departamento, CentroCosto,
    SolicitudCompra, DetalleSolicitudCompra,
    Transferencia, DetalleTransferencia,
)


# =============================================================================
# PRODUCTOS
# =============================================================================

class ProductoForm(forms.ModelForm):
    """
    Formulario para crear y editar productos.
    - stock_actual y stock_minimo se definen como IntegerField para evitar decimales.
    - umbral_alerta permite definir un stock a partir del cual se alerta.
    - precio_unitario conserva decimales (es un monto monetario).
    - Todos los widgets tienen clases de Tailwind.
    """
    # Stock actual: entero, sin decimales
    stock_actual = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={
            "class": "w-full px-3 py-2.5 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition",
            "step": "1",
            "min": "0",
            "inputmode": "numeric",
        }),
        label="Stock actual",
    )

    # Stock mínimo: entero, sin decimales
    stock_minimo = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={
            "class": "w-full px-3 py-2.5 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition",
            "step": "1",
            "min": "0",
            "inputmode": "numeric",
        }),
        label="Stock mínimo",
    )

    # ✅ NUEVO: Umbral de alerta
    umbral_alerta = forms.IntegerField(
        min_value=0,
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={
            "class": "w-full px-3 py-2.5 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition",
            "step": "1",
            "min": "0",
            "inputmode": "numeric",
            "placeholder": "0 = automático (mínimo + 10%)",
        }),
        label="Umbral de alerta",
        help_text="Stock a partir del cual se alerta. Si es 0, se usa stock mínimo + 10%.",
    )

    class Meta:
        model = Producto
        fields = [
            "sku", "nombre", "descripcion", "numero_serie",
            "area", "categoria", "unidad_medida", "estado_fisico", "proveedor",
            "precio_unitario", "stock_actual", "stock_minimo", "umbral_alerta",
            "codigo_barras", "activo",
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={
                "rows": 3,
                "class": "w-full px-3 py-2.5 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition",
            }),
            "sku": forms.TextInput(attrs={
                "class": "w-full px-3 py-2.5 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition",
            }),
            "nombre": forms.TextInput(attrs={
                "class": "w-full px-3 py-2.5 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition",
            }),
            "numero_serie": forms.TextInput(attrs={
                "class": "w-full px-3 py-2.5 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition",
            }),
            "codigo_barras": forms.TextInput(attrs={
                "class": "w-full px-3 py-2.5 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition",
            }),
            "precio_unitario": forms.NumberInput(attrs={
                "class": "w-full px-3 py-2.5 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition",
                "step": "0.01",
                "min": "0",
                "inputmode": "decimal",
            }),
            "area": forms.Select(attrs={
                "class": "w-full px-3 py-2.5 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition appearance-none cursor-pointer",
            }),
            "categoria": forms.Select(attrs={
                "class": "w-full px-3 py-2.5 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition appearance-none cursor-pointer",
            }),
            "unidad_medida": forms.Select(attrs={
                "class": "w-full px-3 py-2.5 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition appearance-none cursor-pointer",
            }),
            "estado_fisico": forms.Select(attrs={
                "class": "w-full px-3 py-2.5 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition appearance-none cursor-pointer",
            }),
            "proveedor": forms.Select(attrs={
                "class": "w-full px-3 py-2.5 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition appearance-none cursor-pointer",
            }),
            "activo": forms.CheckboxInput(attrs={
                "class": "w-4 h-4 text-teal-700 border-gray-300 rounded focus:ring-teal-500",
            }),
        }

    def clean_stock_actual(self):
        valor = self.cleaned_data["stock_actual"]
        if valor is not None and valor < 0:
            raise forms.ValidationError("El stock actual no puede ser negativo.")
        return valor

    def clean_stock_minimo(self):
        valor = self.cleaned_data["stock_minimo"]
        if valor is not None and valor < 0:
            raise forms.ValidationError("El stock mínimo no puede ser negativo.")
        return valor


class ProductoFiltroForm(forms.Form):
    q = forms.CharField(
        label="Código / Descripción / Nº serie",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Buscar por SKU, nombre, serie..."}),
    )
    area = forms.ModelChoiceField(
        queryset=AreaAlmacen.objects.filter(activa=True),
        required=False, empty_label="Todas las áreas",
    )
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.filter(activa=True),
        required=False, empty_label="Todas las categorías",
    )
    estado_fisico = forms.ModelChoiceField(
        queryset=EstadoFisico.objects.filter(activo=True),
        required=False, empty_label="Todos los estados",
    )
    proveedor = forms.ModelChoiceField(
        queryset=Proveedor.objects.filter(activo=True),
        required=False, empty_label="Todos los proveedores",
    )
    stock_estado = forms.ChoiceField(
        label="Estado de stock",
        required=False,
        choices=[
            ("", "Todos"),
            ("bajo_minimo",  "Bajo mínimo"),
            ("cerca_minimo", "Cerca del mínimo"),
            ("sin_stock",    "Sin stock"),
            ("ok",           "Stock OK"),
        ],
    )
    activo = forms.ChoiceField(
        required=False,
        choices=[("", "Todos"), ("1", "Activos"), ("0", "Inactivos")],
    )


# =============================================================================
# MOVIMIENTOS
# =============================================================================

class MovimientoForm(forms.ModelForm):
    class Meta:
        model = MovimientoStock
        fields = [
            "tipo", "area", "proveedor", "departamento", "centro_costo",
            "fecha_movimiento", "motivo", "observacion",
        ]
        widgets = {
            "fecha_movimiento": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "motivo": forms.TextInput(attrs={"placeholder": "Motivo breve del movimiento"}),
            "observacion": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "tipo": "Tipo de movimiento",
            "area": "Área de almacén",
            "proveedor": "Proveedor",
            "departamento": "Departamento",
            "centro_costo": "Centro de costo",
            "fecha_movimiento": "Fecha del movimiento",
            "motivo": "Motivo",
            "observacion": "Observaciones",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["proveedor"].required = False
        self.fields["departamento"].required = False
        self.fields["centro_costo"].required = False
        self.fields["motivo"].required = False
        self.fields["observacion"].required = False
        self.fields["fecha_movimiento"].input_formats = ["%Y-%m-%dT%H:%M"]


# =============================================================================
# COMPRAS — SOLICITUD DE COMPRA
# =============================================================================

class SolicitudCompraForm(forms.ModelForm):
    """
    Formulario de cabecera para crear una solicitud de compra.
    """
    class Meta:
        model = SolicitudCompra
        fields = [
            "area_solicitante", "departamento", "centro_costo", "proveedor",
            "fecha_necesaria", "motivo", "observacion",
        ]
        widgets = {
            "motivo": forms.TextInput(attrs={"placeholder": "Motivo de la solicitud"}),
            "observacion": forms.Textarea(attrs={"rows": 3}),
            "fecha_necesaria": forms.DateInput(attrs={"type": "date"}),
        }
        labels = {
            "area_solicitante": "Área solicitante",
            "departamento": "Departamento",
            "centro_costo": "Centro de costo",
            "proveedor": "Proveedor sugerido",
            "fecha_necesaria": "Fecha requerida",
            "motivo": "Motivo de la solicitud",
            "observacion": "Observaciones",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["departamento"].required = False
        self.fields["centro_costo"].required = False
        self.fields["proveedor"].required = False
        self.fields["fecha_necesaria"].required = False
        self.fields["observacion"].required = False


class DetalleSolicitudCompraForm(forms.ModelForm):
    """Línea de detalle: producto + cantidad + precio estimado."""
    class Meta:
        model = DetalleSolicitudCompra
        fields = ["producto", "cantidad", "precio_estimado", "observacion"]
        widgets = {
            "cantidad": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
            "precio_estimado": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "observacion": forms.TextInput(attrs={"placeholder": "Observación (opcional)"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["producto"].queryset = Producto.objects.filter(activo=True).order_by("nombre")
        self.fields["observacion"].required = False


DetalleSolicitudCompraFormSet = inlineformset_factory(
    SolicitudCompra,
    DetalleSolicitudCompra,
    form=DetalleSolicitudCompraForm,
    extra=3,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class FiltroSolicitudCompraForm(forms.Form):
    """Filtros para el listado de solicitudes."""
    q = forms.CharField(
        label="Buscar",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Número o motivo..."}),
    )
    estado = forms.ChoiceField(
        required=False,
        choices=[("", "Todos los estados")] + list(SolicitudCompra.ESTADOS),
    )
    area = forms.ModelChoiceField(
        queryset=AreaAlmacen.objects.filter(activa=True),
        required=False, empty_label="Todas las áreas",
    )


# =============================================================================
# ÁREAS DE ALMACENAJE
# =============================================================================

class AreaAlmacenForm(forms.ModelForm):
    """Formulario para crear y editar áreas de almacenaje."""
    class Meta:
        model = AreaAlmacen
        fields = ["codigo", "nombre", "descripcion", "activa"]
        widgets = {
            "codigo": forms.TextInput(attrs={
                "placeholder": "Ej: 02564245G1 (o deja 'S/C' si no tienes)"
            }),
            "nombre": forms.TextInput(attrs={
                "placeholder": "Ej: Alimentos (Comedor)"
            }),
            "descripcion": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Descripción del área (opcional)"
            }),
        }
        labels = {
            "codigo": "Código del área",
            "nombre": "Nombre del área",
            "descripcion": "Descripción",
            "activa": "Área activa",
        }

    def clean_codigo(self):
        """Si el código está vacío, asignar 'S/C' automáticamente."""
        codigo = self.cleaned_data.get("codigo", "").strip()
        if not codigo:
            return "S/C"
        return codigo


# =============================================================================
# TRANSFERENCIAS
# =============================================================================

class TransferenciaForm(forms.ModelForm):
    """
    Formulario de cabecera para crear una transferencia entre áreas.
    """
    class Meta:
        model = Transferencia
        fields = [
            "area_origen", "area_destino",
            "fecha_transferencia", "motivo", "observacion",
        ]
        widgets = {
            "fecha_transferencia": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "motivo": forms.TextInput(attrs={
                "placeholder": "Ej: Reorganización de almacén"
            }),
            "observacion": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "area_origen": "Área de origen",
            "area_destino": "Área de destino",
            "fecha_transferencia": "Fecha de transferencia",
            "motivo": "Motivo",
            "observacion": "Observaciones",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["area_origen"].queryset = AreaAlmacen.objects.filter(activa=True).order_by("nombre")
        self.fields["area_destino"].queryset = AreaAlmacen.objects.filter(activa=True).order_by("nombre")
        self.fields["fecha_transferencia"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["observacion"].required = False

    def clean(self):
        cleaned = super().clean()
        origen = cleaned.get("area_origen")
        destino = cleaned.get("area_destino")
        if origen and destino and origen == destino:
            raise forms.ValidationError(
                "El área de origen y destino no pueden ser la misma."
            )
        return cleaned


class DetalleTransferenciaForm(forms.ModelForm):
    """Línea de detalle: producto que se mueve."""
    class Meta:
        model = DetalleTransferencia
        fields = ["producto", "observacion"]
        widgets = {
            "observacion": forms.TextInput(attrs={
                "placeholder": "Observación (opcional)"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["producto"].queryset = Producto.objects.filter(
            activo=True
        ).select_related("area").order_by("area__nombre", "nombre")
        self.fields["observacion"].required = False


# Formset para manejar múltiples productos en una transferencia
DetalleTransferenciaFormSet = inlineformset_factory(
    Transferencia,
    DetalleTransferencia,
    form=DetalleTransferenciaForm,
    extra=3,
    can_delete=True,
    min_num=1,
    validate_min=True,
)