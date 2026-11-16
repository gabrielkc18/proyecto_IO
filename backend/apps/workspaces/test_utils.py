
from uuid import uuid4

from django.contrib.auth import get_user_model

from apps.workspaces.models import Workspace, WorkspaceMembership
from apps.problemas.models import Problema


def crear_workspace_prueba(usuario=None, nombre="Workspace de prueba"):
    """
    Crea un usuario, un workspace y su membresía OWNER.
    Si se proporciona un usuario, reutiliza ese usuario.
    """
    if usuario is None:
        User = get_user_model()
        identificador = uuid4().hex[:8]

        usuario = User.objects.create_user(
            username=f"usuario_{identificador}",
            password="PruebaSegura123!",
        )

    workspace = Workspace.objects.create(
        nombre=nombre,
        propietario=usuario,
    )

    WorkspaceMembership.objects.create(
        workspace=workspace,
        usuario=usuario,
        rol=WorkspaceMembership.Rol.OWNER,
    )

    return usuario, workspace


def crear_problema_prueba(workspace, **datos):
    """
    Crea un problema asociado obligatoriamente a un workspace.
    """
    datos.setdefault("nombre", "Problema de prueba")

    return Problema.objects.create(
        workspace=workspace,
        **datos,
    )
