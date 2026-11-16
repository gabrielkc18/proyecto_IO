
from rest_framework import viewsets

from .models import Producto
from .serializers import ProductoSerializer


class ProductoViewSet(viewsets.ModelViewSet):

    serializer_class = ProductoSerializer

    queryset = Producto.objects.select_related(
        "problema"
    ).all()

    def get_queryset(self):
        queryset = super().get_queryset()

        problema_id = self.request.query_params.get("problema")

        if problema_id:
            queryset = queryset.filter(problema_id=problema_id)

        return queryset

