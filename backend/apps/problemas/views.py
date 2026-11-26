from django.db.models.deletion import ProtectedError
from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response

from apps.workspaces.mixins import WorkspaceContextMixin

from .models import Problema
from .serializers import ProblemaSerializer


class ProblemaViewSet(WorkspaceContextMixin, viewsets.ModelViewSet):
    serializer_class = ProblemaSerializer

    def get_queryset(self):
        return Problema.objects.filter(
            workspace=self.get_workspace()
        ).select_related("workspace").order_by("pk")

    def perform_create(self, serializer):
        serializer.save(workspace=self.get_workspace())

    def destroy(self, request, *args, **kwargs):
        problema = self.get_object()
        try:
            problema.delete()
        except ProtectedError:
            return Response(
                {
                    "detail": (
                        "No se puede eliminar un problema que tiene "
                        "ejecuciones registradas."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
