from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("almacen/", include("apps.almacen.urls", namespace="almacen")),
]