from rest_framework import serializers
from .models import Problema


class ProblemaSerializer(serializers.ModelSerializer):

    class Meta:
        model = Problema
        fields = [
            "id",
            "nombre",
            "descripcion",
            "sentido_objetivo",
            "estado",
            "fecha_creacion",
        ]
        read_only_fields = ["id", "fecha_creacion"]