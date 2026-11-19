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
        validators = []

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

        if self.instance is not None and value.pk != self.instance.problema_id:
            raise serializers.ValidationError(
                "El problema de un producto existente no se puede cambiar."
            )

        return value

    def validate(self, attrs):
        if "codigo" not in attrs:
            return attrs
        problema = attrs.get("problema")
        problema_id = problema.pk if problema is not None else self.instance.problema_id
        productos = Producto.objects.filter(
            problema_id=problema_id,
            codigo=attrs["codigo"],
        )

        if self.instance:
            productos = productos.exclude(pk=self.instance.pk)

        if productos.exists():
            raise serializers.ValidationError({
                "codigo": "Ya existe un producto con ese código en este problema."
            })

        return attrs

    def validate_utilidad_unitaria(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "La utilidad unitaria no puede ser negativa."
            )

        return value
