
from rest_framework import viewsets

from .models import Recurso, ConsumoRecurso
from .serializers import (
    RecursoSerializer,
    ConsumoRecursoSerializer
)


class RecursoViewSet(viewsets.ModelViewSet):

    serializer_class = RecursoSerializer

    queryset = Recurso.objects.select_related(
        "problema"
    ).all()

    def get_queryset(self):
        queryset = super().get_queryset()

        problema_id = self.request.query_params.get("problema")

        if problema_id:
            queryset = queryset.filter(problema_id=problema_id)

        return queryset


class ConsumoRecursoViewSet(viewsets.ModelViewSet):

    serializer_class = ConsumoRecursoSerializer

    queryset = ConsumoRecurso.objects.select_related(
        "producto",
        "recurso",
        "producto__problema",
        "recurso__problema"
    ).all()

    def get_queryset(self):
        queryset = super().get_queryset()

        problema_id = self.request.query_params.get("problema")
        producto_id = self.request.query_params.get("producto")
        recurso_id = self.request.query_params.get("recurso")

        if problema_id:
            queryset = queryset.filter(
                producto__problema_id=problema_id
            )

        if producto_id:
            queryset = queryset.filter(
                producto_id=producto_id
            )

        if recurso_id:
            queryset = queryset.filter(
                recurso_id=recurso_id
            )

        return queryset
