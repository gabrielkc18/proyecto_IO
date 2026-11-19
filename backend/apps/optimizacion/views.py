from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.throttling import ScopedRateThrottle
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema

from apps.workspaces.mixins import WorkspaceContextMixin
from config.api import PlanningConflict, PlanningIdFilter, identificador_positivo
from apps.problemas.models import Problema

from .models import Ejecucion
from .serializers import ComparacionEjecucionesSerializer, EjecucionSerializer
from .services.comparacion import comparar_ejecuciones
from .services.ejecucion import ejecutar_optimizacion


class EjecucionViewSet(
    WorkspaceContextMixin,
    viewsets.ReadOnlyModelViewSet,
):
    serializer_class = EjecucionSerializer
    filter_backends = [PlanningIdFilter]
    id_filters = {"problema": ("problema_id",)}

    def get_queryset(self):
        queryset = Ejecucion.objects.select_related(
            "problema",
            "problema__workspace",
        ).filter(
            problema__workspace=self.get_workspace()
        )

        return queryset.order_by("pk")

    @extend_schema(
        parameters=[OpenApiParameter("contra", int, required=True)],
        responses={
            200: ComparacionEjecucionesSerializer,
            400: OpenApiResponse(description="Identificadores inválidos o problemas distintos."),
            404: OpenApiResponse(description="Ejecución inexistente o fuera del workspace."),
            409: OpenApiResponse(description="Las dos ejecuciones deben ser óptimas y terminadas."),
        },
        description="Compara datos históricos. Los deltas son contra menos base.",
    )
    @action(detail=True, methods=["get"], filter_backends=[])
    def comparar(self, request, pk=None):
        base_id = identificador_positivo(pk, "id")
        contra_id = identificador_positivo(request.query_params.get("contra"), "contra")
        ejecuciones = self.get_queryset().in_bulk([base_id, contra_id])
        if base_id not in ejecuciones or contra_id not in ejecuciones:
            raise NotFound("Una de las ejecuciones no está disponible en el Workspace activo.")

        base, contra = ejecuciones[base_id], ejecuciones[contra_id]
        if base_id == contra_id or base.problema_id != contra.problema_id:
            raise ValidationError({
                "contra": "Selecciona otra ejecución del mismo problema.",
            })
        if any(
            ejecucion.estado_proceso != Ejecucion.EstadoProceso.TERMINADO
            or ejecucion.estado_solver != Ejecucion.EstadoSolver.OPTIMAL
            for ejecucion in (base, contra)
        ):
            raise PlanningConflict("Las dos ejecuciones deben ser óptimas y terminadas.")

        comparacion = comparar_ejecuciones(base, contra)
        return Response(ComparacionEjecucionesSerializer(comparacion).data)


class ProblemaOptimizacionViewSet(
    WorkspaceContextMixin,
    viewsets.GenericViewSet,
):
    queryset = Problema.objects.all()
    serializer_class = EjecucionSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "optimization"

    @action(
        detail=True,
        methods=["post"],
        url_path="ejecutar",
    )
    @extend_schema(
        request=None,
        responses={
            201: EjecucionSerializer,
            400: OpenApiResponse(description="El problema no se puede ejecutar."),
            404: OpenApiResponse(description="Problema no encontrado."),
            429: OpenApiResponse(description="Límite de optimizaciones alcanzado."),
        },
        description=(
            "Ejecuta el problema del workspace activo. Requiere rol "
            "OWNER, ADMIN o EDITOR."
        ),
    )
    def ejecutar(self, request, pk=None):
        problema = Problema.objects.filter(
            pk=identificador_positivo(pk, "id"),
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
