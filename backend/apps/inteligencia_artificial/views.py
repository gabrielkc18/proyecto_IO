from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

from apps.workspaces.mixins import WorkspaceContextMixin
from apps.optimizacion.models import Ejecucion

from .models import AnalisisIA
from .serializers import (
    AnalisisIASerializer,
    GenerarAnalisisSerializer,
)
from .services.analisis import generar_analisis
from .services.proveedor_ia import ErrorProveedorIA


class AnalisisIAViewSet(
    WorkspaceContextMixin,
    viewsets.ReadOnlyModelViewSet,
):
    serializer_class = AnalisisIASerializer

    def get_queryset(self):
        queryset = AnalisisIA.objects.select_related(
            "ejecucion",
            "ejecucion__problema",
            "ejecucion__problema__workspace",
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

        return queryset


class GenerarAnalisisAPIView(WorkspaceContextMixin, APIView):

    def post(self, request, ejecucion_id):
        workspace = self.get_workspace()

        ejecucion = Ejecucion.objects.filter(
            pk=ejecucion_id,
            problema__workspace=workspace,
        ).first()

        if ejecucion is None:
            raise NotFound(
                "La ejecución no existe o no pertenece al Workspace activo."
            )

        serializer = GenerarAnalisisSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pregunta = serializer.validated_data.get("pregunta", "")

        try:
            analisis = generar_analisis(
                ejecucion_id=ejecucion.id,
                pregunta=pregunta,
            )
        except ValueError as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ErrorProveedorIA as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            AnalisisIASerializer(analisis).data,
            status=status.HTTP_201_CREATED,
        )
