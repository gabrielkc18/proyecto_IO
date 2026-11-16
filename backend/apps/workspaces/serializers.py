from rest_framework import serializers

from .models import WorkspaceMembership


class WorkspaceMembershipSerializer(serializers.ModelSerializer):
    workspace_id = serializers.IntegerField(
        source="workspace.id",
        read_only=True,
    )
    nombre = serializers.CharField(
        source="workspace.nombre",
        read_only=True,
    )

    class Meta:
        model = WorkspaceMembership
        fields = (
            "workspace_id",
            "nombre",
            "rol",
            "fecha_creacion",
        )
        read_only_fields = fields
