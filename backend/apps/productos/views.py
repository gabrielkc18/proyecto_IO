from rest_framework import viewsets

from apps.workspaces.mixins import WorkspaceContextMixin
from config.api import PlanningIdFilter, PlanningWriteMixin

from .models import Producto
from .serializers import ProductoSerializer


class ProductoViewSet(WorkspaceContextMixin, PlanningWriteMixin, viewsets.ModelViewSet):
    serializer_class = ProductoSerializer
    filter_backends = [PlanningIdFilter]
    id_filters = {"problema": ("problema_id",)}

    def get_queryset(self):
        queryset = Producto.objects.filter(
            problema__workspace=self.get_workspace()
        ).select_related(
            "problema",
            "problema__workspace",
        )

        return queryset.order_by("pk")
