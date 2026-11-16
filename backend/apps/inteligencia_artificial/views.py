
from rest_framework import viewsets

from .models import AnalisisIA
from .serializers import AnalisisIASerializer


class AnalisisIAViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = AnalisisIASerializer

    queryset = AnalisisIA.objects.select_related(
        "ejecucion",
        "ejecucion__problema"
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

