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


class GenerarAnalisisSerializer(serializers.Serializer):

    pregunta = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=5000,
    )
