from rest_framework import viewsets

from apps.workspaces.mixins import WorkspaceContextMixin

from .models import Producto
from .serializers import ProductoSerializer


class ProductoViewSet(WorkspaceContextMixin, viewsets.ModelViewSet):
    serializer_class = ProductoSerializer

    def get_queryset(self):
        queryset = Producto.objects.filter(
            problema__workspace=self.get_workspace()
        ).select_related(
            "problema",
            "problema__workspace",
        )

        problema_id = self.request.query_params.get("problema")

        if problema_id:
            queryset = queryset.filter(problema_id=problema_id)

        return queryset.order_by("pk")
