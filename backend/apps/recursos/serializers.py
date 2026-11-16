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
            getattr(self.instance, "producto", None)
        )

        recurso = attrs.get(
            "recurso",
            getattr(self.instance, "recurso", None)
        )

        if producto and recurso:
            if producto.problema_id != recurso.problema_id:
                raise serializers.ValidationError(
                    "El producto y el recurso deben pertenecer "
                    "al mismo problema."
                )

        return attrs