from rest_framework import viewsets

from apps.workspaces.mixins import WorkspaceContextMixin
from config.api import PlanningIdFilter, PlanningWriteMixin

from .models import Recurso, ConsumoRecurso
from .serializers import RecursoSerializer, ConsumoRecursoSerializer


class RecursoViewSet(WorkspaceContextMixin, PlanningWriteMixin, viewsets.ModelViewSet):
    serializer_class = RecursoSerializer
    filter_backends = [PlanningIdFilter]
    id_filters = {"problema": ("problema_id",)}

    def get_queryset(self):
        queryset = Recurso.objects.select_related(
            "problema",
            "problema__workspace",
        ).filter(
            problema__workspace=self.get_workspace()
        )

        return queryset.order_by("pk")


class ConsumoRecursoViewSet(
    WorkspaceContextMixin,
    PlanningWriteMixin,
    viewsets.ModelViewSet,
):
    serializer_class = ConsumoRecursoSerializer
    filter_backends = [PlanningIdFilter]
    id_filters = {
        "problema": ("producto__problema_id", "recurso__problema_id"),
        "producto": ("producto_id",),
        "recurso": ("recurso_id",),
    }

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

        return queryset.order_by("pk")
