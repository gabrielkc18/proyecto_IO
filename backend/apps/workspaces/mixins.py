from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import SAFE_METHODS

from apps.workspaces.models import Workspace, WorkspaceMembership


class WorkspaceContextMixin:
    """
    Resuelve el Workspace activo mediante X-Workspace-ID.
    La pertenencia se valida contra la membresía del usuario.
    """

    workspace_header = "X-Workspace-ID"

    def get_membership(self):
        if not self.request.user or not self.request.user.is_authenticated:
            raise NotFound("Workspace no disponible.")

        if hasattr(self, "_workspace_membership"):
            return self._workspace_membership

        workspace_id = self.request.headers.get(self.workspace_header)

        if not workspace_id:
            raise ValidationError({
                "workspace": "Debes enviar X-Workspace-ID."
            })

        try:
            workspace_id = int(workspace_id)
        except (TypeError, ValueError):
            raise ValidationError({
                "workspace": "El identificador del Workspace no es válido."
            })

        membership = WorkspaceMembership.objects.select_related(
            "workspace"
        ).filter(
            workspace_id=workspace_id,
            usuario=self.request.user,
        ).first()

        if membership is None:
            raise NotFound(
                "Workspace inexistente o sin acceso para este usuario."
            )

        self._workspace_membership = membership
        return membership

    def get_workspace(self):
        if getattr(self, "swagger_fake_view", False):
            return Workspace(pk=0)
        return self.get_membership().workspace

    def get_workspace_role(self):
        return self.get_membership().rol

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["workspace"] = self.get_workspace()
        return context

    def check_workspace_write_permission(self):
        """
        OWNER, ADMIN y EDITOR pueden modificar.
        VIEWER solamente puede consultar.
        """
        if self.request.method in SAFE_METHODS:
            return

        allowed_roles = {
            WorkspaceMembership.Rol.OWNER,
            WorkspaceMembership.Rol.ADMIN,
            WorkspaceMembership.Rol.EDITOR,
        }

        if self.get_workspace_role() not in allowed_roles:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "Tu rol no permite modificar este Workspace."
            )

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        # Validar Workspace en todos los endpoints que usan este mixin.
        self.get_workspace()

        # Aplicar RBAC antes de ejecutar la acción.
        self.check_workspace_write_permission()
