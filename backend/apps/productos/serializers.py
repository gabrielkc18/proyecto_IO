from rest_framework import serializers
from .models import Producto


class ProductoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Producto
        fields = [
            "id",
            "problema",
            "codigo",
            "nombre",
            "descripcion",
            "utilidad_unitaria",
            "activo",
        ]
        read_only_fields = ["id"]

    def validate_utilidad_unitaria(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "La utilidad unitaria no puede ser negativa."
            )

        return value