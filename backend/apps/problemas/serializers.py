
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
        validators = []

    def validate_nombre(self, value):
        workspace = self.context.get("workspace")

        # En pruebas aisladas del serializer puede no existir
        # todavía el contexto de Workspace.
        if workspace is None:
            return value

        problemas_existentes = Problema.objects.filter(
            workspace=workspace,
            nombre=value,
        )

        if self.instance:
            problemas_existentes = problemas_existentes.exclude(
                pk=self.instance.pk
            )

        if problemas_existentes.exists():
            raise serializers.ValidationError(
                "Ya existe un problema con ese nombre en este Workspace."
            )

        return value
