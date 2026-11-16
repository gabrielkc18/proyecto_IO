from rest_framework import serializers
from .models import ResultadoProducto, ResultadoRecurso


class ResultadoProductoSerializer(serializers.ModelSerializer):

    class Meta:
        model = ResultadoProducto
        fields = [
            "id",
            "ejecucion",
            "producto",
            "nombre_producto",
            "utilidad_unitaria",
            "cantidad",
            "utilidad_aportada",
        ]
        read_only_fields = fields


class ResultadoRecursoSerializer(serializers.ModelSerializer):

    class Meta:
        model = ResultadoRecurso
        fields = [
            "id",
            "ejecucion",
            "recurso",
            "nombre_recurso",
            "unidad_medida",
            "disponibilidad",
            "consumo_total",
            "holgura",
            "estado_uso",
        ]
        read_only_fields = fields