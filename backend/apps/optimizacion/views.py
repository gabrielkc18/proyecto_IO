
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Ejecucion
from .serializers import EjecucionSerializer
from apps.problemas.models import Problema
from apps.optimizacion.services.ejecucion import ejecutar_optimizacion


class EjecucionViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = EjecucionSerializer

    queryset = Ejecucion.objects.select_related(
        "problema"
    ).all()

    def get_queryset(self):
        queryset = super().get_queryset()

        problema_id = self.request.query_params.get("problema")

        if problema_id:
            queryset = queryset.filter(
                problema_id=problema_id
            )

        return queryset


class ProblemaOptimizacionViewSet(viewsets.ViewSet):

    @action(
        detail=True,
        methods=["post"],
        url_path="ejecutar",
    )
    def ejecutar(self, request, pk=None):

        try:
            problema = Problema.objects.get(pk=pk)
        except Problema.DoesNotExist:
            return Response(
                {"error": "El problema solicitado no existe."},
                status=status.HTTP_404_NOT_FOUND,
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
