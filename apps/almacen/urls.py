from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = "almacen"

urlpatterns = [
    # Dashboard / raíz
    path("",                                     views.home,                                name="home"),

    # Productos — CRUD
    path("productos/",                           views.ProductoListView.as_view(),          name="producto_list"),
    path("productos/nuevo/",                     views.ProductoCreateView.as_view(),        name="producto_create"),

    # ⭐ RUTA PARA EXPORTAR (antes de las que tienen <uuid>)
    path("productos/exportar/",                  views.exportar_productos_excel,            name="producto_exportar"),

    path("productos/<uuid:codigo_qr>/",          views.ProductoDetailView.as_view(),        name="producto_detail"),
    path("productos/<uuid:codigo_qr>/editar/",   views.ProductoUpdateView.as_view(),        name="producto_update"),
    path("productos/<uuid:codigo_qr>/eliminar/", views.ProductoDeleteView.as_view(),        name="producto_delete"),
    path("productos/<uuid:codigo_qr>/qr/",       views.producto_qr,                         name="producto_qr"),

    # ✅ Desactivar / Reactivar (sin eliminar)
    path("productos/<uuid:codigo_qr>/desactivar/", views.producto_desactivar,               name="producto_desactivar"),
    path("productos/<uuid:codigo_qr>/activar/",    views.producto_activar,                  name="producto_activar"),

    # Movimientos
    path("movimientos/",                         views.MovimientoListView.as_view(),        name="movimiento_list"),
    path("movimientos/exportar/",                views.exportar_movimientos_excel,          name="movimiento_exportar"),
    path("movimientos/<str:numero>/",            views.MovimientoDetailView.as_view(),      name="movimiento_detail"),

    # Áreas de almacenaje
    path("areas/",                               views.AreaAlmacenListView.as_view(),       name="area_list"),
    path("areas/nueva/",                         views.AreaAlmacenCreateView.as_view(),     name="area_create"),
    path("areas/<int:pk>/editar/",               views.AreaAlmacenUpdateView.as_view(),     name="area_update"),
    path("areas/<int:pk>/eliminar/",             views.AreaAlmacenDeleteView.as_view(),     name="area_delete"),

    # Reportes
    path("reportes/",                            views.ReportesView.as_view(),              name="reportes"),

    # Transferencias
    path("transferencias/",                              views.TransferenciaListView.as_view(),   name="transferencia_list"),
    path("transferencias/nueva/",                        views.TransferenciaCreateView.as_view(), name="transferencia_create"),
    path("transferencias/<str:numero>/",                 views.TransferenciaDetailView.as_view(), name="transferencia_detail"),
    path("transferencias/<str:numero>/editar/",          views.TransferenciaUpdateView.as_view(), name="transferencia_update"),
    path("transferencias/<str:numero>/eliminar/",        views.TransferenciaDeleteView.as_view(), name="transferencia_delete"),
    path("transferencias/<str:numero>/confirmar/",       views.transferencia_confirmar,           name="transferencia_confirmar"),
    path("transferencias/<str:numero>/anular/",          views.transferencia_anular,              name="transferencia_anular"),

    # Compras — Solicitudes
    path("compras/",                              views.SolicitudCompraListView.as_view(),   name="solicitud_compra_list"),
    path("compras/nueva/",                        views.SolicitudCompraCreateView.as_view(), name="solicitud_compra_create"),
    path("compras/<str:numero>/",                 views.SolicitudCompraDetailView.as_view(), name="solicitud_compra_detail"),
    path("compras/<str:numero>/editar/",          views.SolicitudCompraUpdateView.as_view(), name="solicitud_compra_update"),
    path("compras/<str:numero>/eliminar/",        views.SolicitudCompraDeleteView.as_view(), name="solicitud_compra_delete"),
    path("compras/<str:numero>/aprobar/",         views.solicitud_compra_aprobar,             name="solicitud_compra_aprobar"),
    path("compras/<str:numero>/rechazar/",        views.solicitud_compra_rechazar,            name="solicitud_compra_rechazar"),
    path("compras/<str:numero>/marcar-comprada/", views.solicitud_compra_marcar_comprada,     name="solicitud_compra_marcar_comprada"),

    # ✅ Notificaciones
    path("notificaciones/marcar-leidas/",         views.notificaciones_marcar_leidas,        name="notificaciones_marcar_leidas"),
    path("notificaciones/<int:pk>/marcar-leida/", views.notificacion_marcar_leida,           name="notificacion_marcar_leida"),

    # Escaneo QR
    path("escanear/",                            views.escanear_qr,                         name="escanear"),

    # ✅ Autenticación (login / logout / cambio de contraseña)
    path("accounts/login/",
         auth_views.LoginView.as_view(template_name="registration/login.html"),
         name="login"),
    path("accounts/logout/",
         auth_views.LogoutView.as_view(next_page="almacen:login"),
         name="logout"),
    path("accounts/password_change/",
         auth_views.PasswordChangeView.as_view(
             template_name="registration/password_change_form.html",
             success_url=reverse_lazy("almacen:password_change_done")
         ),
         name="password_change"),
    path("accounts/password_change/done/",
         auth_views.PasswordChangeDoneView.as_view(
             template_name="registration/password_change_done.html"
         ),
         name="password_change_done"),
]