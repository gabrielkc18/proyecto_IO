from rest_framework import viewsets

from apps.workspaces.mixins import WorkspaceContextMixin

from .models import Recurso, ConsumoRecurso
from .serializers import RecursoSerializer, ConsumoRecursoSerializer


class RecursoViewSet(WorkspaceContextMixin, viewsets.ModelViewSet):
    serializer_class = RecursoSerializer

    def get_queryset(self):
        queryset = Recurso.objects.select_related(
            "problema",
            "problema__workspace",
        ).filter(
            problema__workspace=self.get_workspace()
        )

        problema_id = self.request.query_params.get("problema")

        if problema_id:
            queryset = queryset.filter(problema_id=problema_id)

        return queryset.order_by("pk")


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

        return queryset.order_by("pk")
