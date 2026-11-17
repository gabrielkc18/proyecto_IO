from django.contrib.auth import get_user_model
from django.db import transaction

from .models import Workspace, WorkspaceMembership


@transaction.atomic
def obtener_o_crear_workspace_personal(usuario):
    usuario = get_user_model().objects.select_for_update().get(pk=usuario.pk)
    workspaces_propios = Workspace.objects.filter(
        propietario=usuario,
    ).order_by("pk")

    if workspaces_propios.count() > 1:
        raise ValueError(
            "No se puede determinar un único workspace personal existente."
        )

    workspace = workspaces_propios.first()
    if workspace is not None:
        membership = WorkspaceMembership.objects.filter(
            workspace=workspace,
            usuario=usuario,
        ).first()
        if membership is None:
            WorkspaceMembership.objects.create(
                workspace=workspace,
                usuario=usuario,
                rol=WorkspaceMembership.Rol.OWNER,
            )
        elif membership.rol != WorkspaceMembership.Rol.OWNER:
            raise ValueError(
                "El propietario del workspace no tiene rol OWNER."
            )
        return workspace

    if WorkspaceMembership.objects.filter(
        usuario=usuario,
        rol=WorkspaceMembership.Rol.OWNER,
    ).exists():
        raise ValueError(
            "El usuario ya tiene una membresía OWNER sin ser propietario."
        )

    workspace = Workspace.objects.create(
        nombre=f"Personal de {usuario.username}"[:150],
        propietario=usuario,
    )
    WorkspaceMembership.objects.create(
        workspace=workspace,
        usuario=usuario,
        rol=WorkspaceMembership.Rol.OWNER,
    )
    return workspace
