from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework.throttling import ScopedRateThrottle
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
)

from apps.workspaces.mixins import WorkspaceContextMixin
from apps.optimizacion.models import Ejecucion

from .models import AnalisisIA
from .serializers import (
    AnalisisIASerializer,
    GenerarAnalisisSerializer,
)
from .services.analisis import ConflictoIdempotencia, generar_analisis
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

        return queryset.order_by("pk")


class GenerarAnalisisAPIView(WorkspaceContextMixin, APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai_analysis"

    @extend_schema(
        tags=["Análisis IA"],
        parameters=[
            OpenApiParameter(
                name="Idempotency-Key",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.HEADER,
                required=True,
                description=(
                    "UUID único de esta solicitud. Un reintento exitoso con "
                    "la misma clave y payload reutiliza el análisis existente."
                ),
            )
        ],
        request=GenerarAnalisisSerializer,
        responses={
            200: AnalisisIASerializer,
            201: AnalisisIASerializer,
            400: OpenApiResponse(
                description="Falta consentimiento o los datos son inválidos."
            ),
            404: OpenApiResponse(
                description="Ejecución inexistente o fuera del workspace."
            ),
            409: OpenApiResponse(
                description="Clave idempotente en conflicto o ya procesada."
            ),
            502: OpenApiResponse(
                description="El proveedor de IA no pudo completar la solicitud."
            ),
        },
        description=(
            "Requiere consentimiento explícito en el cuerpo y el encabezado "
            "X-Workspace-ID. Solo envía contexto minimizado a Groq; no incluyas "
            "datos personales ni secretos en la pregunta."
        ),
    )
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

        serializer = GenerarAnalisisSerializer(
            data=request.data,
            context={
                "idempotency_key": request.headers.get("Idempotency-Key"),
            },
        )
        serializer.is_valid(raise_exception=True)

        pregunta = serializer.validated_data.get("pregunta", "")

        try:
            analisis, replay = generar_analisis(
                ejecucion_id=ejecucion.id,
                pregunta=pregunta,
                consentimiento_confirmado=(
                    serializer.validated_data["consentimiento_confirmado"]
                ),
                solicitante=request.user,
                clave_idempotencia=serializer.validated_data[
                    "idempotency_key"
                ],
            )
        except ConflictoIdempotencia as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_409_CONFLICT,
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
            status=(
                status.HTTP_200_OK
                if replay
                else status.HTTP_201_CREATED
            ),
        )
