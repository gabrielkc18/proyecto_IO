from rest_framework import serializers
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