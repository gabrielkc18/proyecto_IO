from rest_framework import viewsets

from apps.workspaces.mixins import WorkspaceContextMixin
from config.api import PlanningWriteMixin

from .models import Problema
from .serializers import ProblemaSerializer


class ProblemaViewSet(WorkspaceContextMixin, PlanningWriteMixin, viewsets.ModelViewSet):
    serializer_class = ProblemaSerializer

    def get_queryset(self):
        return Problema.objects.filter(
            workspace=self.get_workspace()
        ).select_related("workspace").order_by("pk")

    def perform_create(self, serializer):
        serializer.save(workspace=self.get_workspace())
