from rest_framework import viewsets

from apps.workspaces.mixins import WorkspaceContextMixin
from config.api import PlanningIdFilter

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
    filter_backends = [PlanningIdFilter]
    id_filters = {
        "ejecucion": ("ejecucion_id",),
        "problema": ("ejecucion__problema_id",),
    }

    def get_queryset(self):
        queryset = ResultadoProducto.objects.select_related(
            "ejecucion",
            "ejecucion__problema",
            "ejecucion__problema__workspace",
            "producto",
        ).filter(
            ejecucion__problema__workspace=self.get_workspace()
        )

        return queryset.order_by("pk")


class ResultadoRecursoViewSet(
    WorkspaceContextMixin,
    viewsets.ReadOnlyModelViewSet,
):
    serializer_class = ResultadoRecursoSerializer
    filter_backends = [PlanningIdFilter]
    id_filters = {
        "ejecucion": ("ejecucion_id",),
        "problema": ("ejecucion__problema_id",),
    }

    def get_queryset(self):
        queryset = ResultadoRecurso.objects.select_related(
            "ejecucion",
            "ejecucion__problema",
            "ejecucion__problema__workspace",
            "recurso",
        ).filter(
            ejecucion__problema__workspace=self.get_workspace()
        )

        return queryset.order_by("pk")
