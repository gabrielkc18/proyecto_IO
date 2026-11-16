from rest_framework import viewsets
from rest_framework.exceptions import ValidationError, NotFound

from apps.workspaces.models import Workspace

from .models import Recurso, ConsumoRecurso
from .serializers import (
    RecursoSerializer,
    ConsumoRecursoSerializer,
)


class WorkspaceContextMixin:

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
                "workspace": "El identificador del Workspace no es válido."
            })

        workspace = Workspace.objects.filter(
            pk=workspace_id,
            membresias__usuario=self.request.user,
        ).first()

        if workspace is None:
            raise NotFound(
                "El Workspace no existe o no tienes acceso a él."
            )

        return workspace

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["workspace"] = self.get_workspace()
        return context


class RecursoViewSet(WorkspaceContextMixin, viewsets.ModelViewSet):

    serializer_class = RecursoSerializer

    def get_queryset(self):
        workspace = self.get_workspace()

        queryset = Recurso.objects.select_related(
            "problema",
            "problema__workspace",
        ).filter(
            problema__workspace=workspace,
        )

        problema_id = self.request.query_params.get("problema")

        if problema_id:
            queryset = queryset.filter(problema_id=problema_id)

        return queryset


class ConsumoRecursoViewSet(
    WorkspaceContextMixin,
    viewsets.ModelViewSet,
):

    serializer_class = ConsumoRecursoSerializer

    def get_queryset(self):
        workspace = self.get_workspace()

        queryset = ConsumoRecurso.objects.select_related(
            "producto",
            "recurso",
            "producto__problema",
            "recurso__problema",
            "producto__problema__workspace",
            "recurso__problema__workspace",
        ).filter(
            producto__problema__workspace=workspace,
            recurso__problema__workspace=workspace,
        )

        problema_id = self.request.query_params.get("problema")
        producto_id = self.request.query_params.get("producto")
        recurso_id = self.request.query_params.get("recurso")

        if problema_id:
            queryset = queryset.filter(
                producto__problema_id=problema_id,
                recurso__problema_id=problema_id,
            )

        if producto_id:
            queryset = queryset.filter(producto_id=producto_id)

        if recurso_id:
            queryset = queryset.filter(recurso_id=recurso_id)

        return queryset
