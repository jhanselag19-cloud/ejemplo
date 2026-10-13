from django.apps import AppConfig

class AlmacenConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.almacen"          # ← con el prefijo "apps."
    label = "almacen"              # ← label corto para evitar conflictos
    verbose_name = "Almacén"