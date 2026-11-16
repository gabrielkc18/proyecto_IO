
from rest_framework import viewsets
from rest_framework.exceptions import NotFound, ValidationError

from apps.workspaces.models import Workspace

from .models import Problema
from .serializers import ProblemaSerializer


class ProblemaViewSet(viewsets.ModelViewSet):

    serializer_class = ProblemaSerializer

    def get_workspace(self):
        workspace_id = self.request.headers.get("X-Workspace-ID")

        if not workspace_id:
            raise ValidationError({
                "workspace": "Debes enviar el encabezado X-Workspace-ID."
            })

        try:
            workspace_id = int(workspace_id)
        except (TypeError, ValueError):
            raise ValidationError({
                "workspace": "El X-Workspace-ID debe ser un número entero."
            })

        workspace = Workspace.objects.filter(
            pk=workspace_id,
            membresias__usuario=self.request.user,
        ).first()

        if workspace is None:
            raise NotFound(
                "Workspace inexistente o sin acceso para este usuario."
            )

        return workspace

    def get_queryset(self):
        workspace = self.get_workspace()

        return Problema.objects.filter(
            workspace=workspace
        ).select_related("workspace")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["workspace"] = self.get_workspace()
        return context

    def perform_create(self, serializer):
        workspace = self.get_workspace()
        serializer.save(workspace=workspace)
