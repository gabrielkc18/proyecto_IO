from rest_framework import viewsets

from apps.workspaces.mixins import WorkspaceContextMixin

from .models import ResultadoProducto, ResultadoRecurso
from .serializers import (
    ResultadoProductoSerializer,
    ResultadoRecursoSerializer,
)


class ResultadoProductoViewSet(
    WorkspaceContextMixin,
    viewsets.ReadOnlyModelViewSet,
):
    serializer_class = ResultadoProductoSerializer

    def get_queryset(self):
        queryset = ResultadoProducto.objects.select_related(
            "ejecucion",
            "ejecucion__problema",
            "ejecucion__problema__workspace",
            "producto",
        ).filter(
            ejecucion__problema__workspace=self.get_workspace()
        )

        ejecucion_id = self.request.query_params.get("ejecucion")
        problema_id = self.request.query_params.get("problema")

        if ejecucion_id:
            queryset = queryset.filter(ejecucion_id=ejecucion_id)

        if problema_id:
            queryset = queryset.filter(
                ejecucion__problema_id=problema_id
            )

        return queryset.order_by("pk")


class ResultadoRecursoViewSet(
    WorkspaceContextMixin,
    viewsets.ReadOnlyModelViewSet,
):
    serializer_class = ResultadoRecursoSerializer

    def get_queryset(self):
        queryset = ResultadoRecurso.objects.select_related(
            "ejecucion",
            "ejecucion__problema",
            "ejecucion__problema__workspace",
            "recurso",
        ).filter(
            ejecucion__problema__workspace=self.get_workspace()
        )

        ejecucion_id = self.request.query_params.get("ejecucion")
        problema_id = self.request.query_params.get("problema")

        if ejecucion_id:
            queryset = queryset.filter(ejecucion_id=ejecucion_id)

        if problema_id:
            queryset = queryset.filter(
                ejecucion__problema_id=problema_id
            )

        return queryset.order_by("pk")
