from rest_framework import serializers

from .models import Recurso, ConsumoRecurso


class RecursoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recurso
        fields = [
            "id",
            "problema",
            "nombre",
            "unidad_medida",
            "disponibilidad",
            "activo",
        ]
        read_only_fields = ["id"]

    def validate_problema(self, value):
        workspace = self.context.get("workspace")

        if workspace is None:
            raise serializers.ValidationError(
                "No se ha definido un Workspace válido."
            )

        if value.workspace_id != workspace.pk:
            raise serializers.ValidationError(
                "El problema no pertenece al Workspace activo."
            )

        if self.instance is not None and value.pk != self.instance.problema_id:
            raise serializers.ValidationError(
                "El problema de un recurso existente no se puede cambiar."
            )

        return value

    def validate_disponibilidad(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "La disponibilidad no puede ser negativa."
            )
        return value


class ConsumoRecursoSerializer(serializers.ModelSerializer):

    class Meta:
        model = ConsumoRecurso
        fields = [
            "id",
            "producto",
            "recurso",
            "cantidad_por_unidad",
        ]
        read_only_fields = ["id"]

    def validate_cantidad_por_unidad(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "La cantidad por unidad no puede ser negativa."
            )
        return value

    def validate(self, attrs):
        producto = attrs.get(
            "producto",
            getattr(self.instance, "producto", None),
        )
        recurso = attrs.get(
            "recurso",
            getattr(self.instance, "recurso", None),
        )
        workspace = self.context.get("workspace")

        if workspace is None:
            raise serializers.ValidationError(
                "No se ha definido un Workspace válido."
            )

        if producto and producto.problema.workspace_id != workspace.pk:
            raise serializers.ValidationError({
                "producto": "El producto no pertenece al Workspace activo."
            })

        if recurso and recurso.problema.workspace_id != workspace.pk:
            raise serializers.ValidationError({
                "recurso": "El recurso no pertenece al Workspace activo."
            })

        if producto and recurso:
            if producto.problema_id != recurso.problema_id:
                raise serializers.ValidationError(
                    "El producto y el recurso deben pertenecer "
                    "al mismo problema."
                )

        return attrs
