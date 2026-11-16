
from rest_framework import viewsets

from .models import ResultadoProducto, ResultadoRecurso
from .serializers import (
    ResultadoProductoSerializer,
    ResultadoRecursoSerializer
)


class ResultadoProductoViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = ResultadoProductoSerializer

    queryset = ResultadoProducto.objects.select_related(
        "ejecucion",
        "ejecucion__problema",
        "producto"
    ).all()

    def get_queryset(self):
        queryset = super().get_queryset()

        ejecucion_id = self.request.query_params.get("ejecucion")
        problema_id = self.request.query_params.get("problema")

        if ejecucion_id:
            queryset = queryset.filter(
                ejecucion_id=ejecucion_id
            )

        if problema_id:
            queryset = queryset.filter(
                ejecucion__problema_id=problema_id
            )

        return queryset


class ResultadoRecursoViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = ResultadoRecursoSerializer

    queryset = ResultadoRecurso.objects.select_related(
        "ejecucion",
        "ejecucion__problema",
        "recurso"
    ).all()

    def get_queryset(self):
        queryset = super().get_queryset()

        ejecucion_id = self.request.query_params.get("ejecucion")
        problema_id = self.request.query_params.get("problema")

        if ejecucion_id:
            queryset = queryset.filter(
                ejecucion_id=ejecucion_id
            )

        if problema_id:
            queryset = queryset.filter(
                ejecucion__problema_id=problema_id
            )

        return queryset

