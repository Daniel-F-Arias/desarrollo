from .models import AccionUsuario

def registrar_accion(usuario, accion, detalle=""):
    """
    Guarda una acción realizada por un usuario en la base de datos.
    """
    if usuario.is_authenticated:
        AccionUsuario.objects.create(usuario=usuario, accion=accion, detalle=detalle)
