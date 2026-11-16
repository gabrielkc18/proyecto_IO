from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

from apps.workspaces.mixins import WorkspaceContextMixin
from apps.problemas.models import Problema

from .models import Ejecucion
from .serializers import EjecucionSerializer
from .services.ejecucion import ejecutar_optimizacion


class EjecucionViewSet(
    WorkspaceContextMixin,
    viewsets.ReadOnlyModelViewSet,
):
    serializer_class = EjecucionSerializer

    def get_queryset(self):
        queryset = Ejecucion.objects.select_related(
            "problema",
            "problema__workspace",
        ).filter(
            problema__workspace=self.get_workspace()
        )

        problema_id = self.request.query_params.get("problema")

        if problema_id:
            queryset = queryset.filter(problema_id=problema_id)

        return queryset


class ProblemaOptimizacionViewSet(
    WorkspaceContextMixin,
    viewsets.GenericViewSet,
):
    queryset = Problema.objects.all()

    @action(
        detail=True,
        methods=["post"],
        url_path="ejecutar",
    )
    def ejecutar(self, request, pk=None):
        problema = Problema.objects.filter(
            pk=pk,
            workspace=self.get_workspace(),
        ).first()

        if problema is None:
            raise NotFound(
                "El problema no existe o no pertenece al Workspace activo."
            )

        try:
            ejecucion = ejecutar_optimizacion(problema.id)
        except ValueError as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            EjecucionSerializer(ejecucion).data,
            status=status.HTTP_201_CREATED,
        )
