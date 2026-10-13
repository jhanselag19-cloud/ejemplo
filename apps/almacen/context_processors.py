from .models import Notificacion


def notificaciones_context(request):
    """
    Añade al contexto de todos los templates:
    - notificaciones_no_leidas: cantidad de notificaciones no leídas
    - notificaciones_ultimas: las últimas 10 notificaciones
    """
    if not request.user.is_authenticated:
        return {
            "notificaciones_no_leidas": 0,
            "notificaciones_ultimas": [],
        }

    qs = Notificacion.objects.filter(
        usuario=request.user
    ).order_by("-creado_en")

    return {
        "notificaciones_no_leidas": qs.filter(leida=False).count(),
        "notificaciones_ultimas": qs[:10],
    }