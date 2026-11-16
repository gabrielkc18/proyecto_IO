from rest_framework import viewsets
from rest_framework.exceptions import NotFound, ValidationError

from apps.workspaces.models import Workspace

from .models import Producto
from .serializers import ProductoSerializer


class ProductoViewSet(viewsets.ModelViewSet):

    serializer_class = ProductoSerializer

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

        queryset = Producto.objects.filter(
            problema__workspace=workspace
        ).select_related(
            "problema",
            "problema__workspace",
        )

        problema_id = self.request.query_params.get("problema")

        if problema_id:
            queryset = queryset.filter(
                problema_id=problema_id
            )

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["workspace"] = self.get_workspace()
        return context
