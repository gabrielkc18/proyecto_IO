from rest_framework import serializers
from .models import AnalisisIA


class AnalisisIASerializer(serializers.ModelSerializer):

    class Meta:
        model = AnalisisIA
        fields = [
            "id",
            "ejecucion",
            "tipo_analisis",
            "pregunta",
            "contenido",
            "modelo_ia",
            "fecha_generacion",
            "contexto_enviado",
        ]
        read_only_fields = fields