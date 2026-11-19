from rest_framework import serializers

from apps.problemas.models import Problema
from apps.resultados.serializers import ResultadoProductoSerializer, ResultadoRecursoSerializer

from .models import Ejecucion


class EjecucionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ejecucion
        fields = [
            "id",
            "problema",
            "fecha_inicio",
            "fecha_fin",
            "estado_proceso",
            "estado_solver",
            "utilidad_total",
            "solver_nombre",
            "mensaje_error",
            "snapshot_entrada",
        ]

        read_only_fields = fields


class ResumenEjecucionComparadaSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    sentido_objetivo = serializers.ChoiceField(
        choices=Problema.SentidoObjetivo.choices, allow_null=True,
    )
    utilidad_total = serializers.DecimalField(max_digits=16, decimal_places=2, allow_null=True)


class DeltaProductoSerializer(serializers.Serializer):
    cantidad = serializers.IntegerField()
    utilidad_aportada = serializers.DecimalField(max_digits=17, decimal_places=2)


class DeltaRecursoSerializer(serializers.Serializer):
    consumo_total = serializers.DecimalField(max_digits=15, decimal_places=2)
    holgura = serializers.DecimalField(max_digits=15, decimal_places=2)


class ProductoComparadoSerializer(serializers.Serializer):
    producto_id = serializers.IntegerField()
    base = ResultadoProductoSerializer(allow_null=True)
    contra = ResultadoProductoSerializer(allow_null=True)
    delta = DeltaProductoSerializer(allow_null=True)


class RecursoComparadoSerializer(serializers.Serializer):
    recurso_id = serializers.IntegerField()
    base = ResultadoRecursoSerializer(allow_null=True)
    contra = ResultadoRecursoSerializer(allow_null=True)
    delta = DeltaRecursoSerializer(allow_null=True)


class ComparacionEjecucionesSerializer(serializers.Serializer):
    problema = serializers.IntegerField()
    base = ResumenEjecucionComparadaSerializer()
    contra = ResumenEjecucionComparadaSerializer()
    delta_utilidad_total = serializers.DecimalField(
        max_digits=17, decimal_places=2, allow_null=True,
    )
    productos = ProductoComparadoSerializer(many=True)
    recursos = RecursoComparadoSerializer(many=True)
