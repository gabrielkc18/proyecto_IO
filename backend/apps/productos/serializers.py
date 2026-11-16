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

    def validate_problema(self, value):
        workspace = self.context.get("workspace")

        if workspace is None:
            raise serializers.ValidationError(
                "No se ha establecido un Workspace autorizado."
            )

        if value.workspace_id != workspace.pk:
            raise serializers.ValidationError(
                "El problema no pertenece al Workspace seleccionado."
            )

        return value

    def validate_codigo(self, value):
        problema = self.initial_data.get("problema")

        if problema is None:
            return value

        try:
            problema_id = int(problema)
        except (TypeError, ValueError):
            return value

        productos = Producto.objects.filter(
            problema_id=problema_id,
            codigo=value,
        )

        if self.instance:
            productos = productos.exclude(pk=self.instance.pk)

        if productos.exists():
            raise serializers.ValidationError(
                "Ya existe un producto con ese código en este problema."
            )

        return value

    def validate_utilidad_unitaria(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "La utilidad unitaria no puede ser negativa."
            )

        return value
