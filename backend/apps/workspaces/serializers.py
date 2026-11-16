from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import WorkspaceMembership


User = get_user_model()


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


class WorkspaceMemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source="usuario.username",
        read_only=True,
    )

    class Meta:
        model = WorkspaceMembership
        fields = (
            "id",
            "username",
            "rol",
            "fecha_creacion",
        )
        read_only_fields = fields


class WorkspaceMemberCreateSerializer(serializers.Serializer):
    username = serializers.SlugRelatedField(
        source="usuario",
        slug_field="username",
        queryset=User.objects.filter(is_active=True),
        error_messages={
            "does_not_exist": "No existe un usuario activo con ese username.",
            "invalid": "Debes enviar un username válido.",
        },
    )
    rol = serializers.ChoiceField(
        choices=(
            WorkspaceMembership.Rol.ADMIN,
            WorkspaceMembership.Rol.EDITOR,
            WorkspaceMembership.Rol.VIEWER,
        ),
    )

    def validate(self, attrs):
        workspace = self.context.get("workspace")
        if workspace is None:
            raise serializers.ValidationError(
                {"workspace": "No se ha establecido un Workspace válido."}
            )

        if WorkspaceMembership.objects.filter(
            workspace=workspace,
            usuario=attrs["usuario"],
        ).exists():
            raise serializers.ValidationError(
                {"username": "El usuario ya pertenece a este Workspace."}
            )

        if (
            self.context.get("actor_role") == WorkspaceMembership.Rol.ADMIN
            and attrs["rol"] == WorkspaceMembership.Rol.ADMIN
        ):
            raise serializers.ValidationError(
                {"rol": "Un ADMIN no puede asignar el rol ADMIN."}
            )

        return attrs


class WorkspaceMemberRoleSerializer(serializers.Serializer):
    rol = serializers.ChoiceField(
        choices=(
            WorkspaceMembership.Rol.ADMIN,
            WorkspaceMembership.Rol.EDITOR,
            WorkspaceMembership.Rol.VIEWER,
        ),
    )

    def validate(self, attrs):
        if self.instance is None:
            raise serializers.ValidationError(
                "Se requiere una membresía para cambiar su rol."
            )

        if (
            self.instance.rol == WorkspaceMembership.Rol.OWNER
            or self.instance.usuario_id == self.instance.workspace.propietario_id
        ):
            raise serializers.ValidationError(
                "La propiedad solo puede cambiarse mediante transferencia."
            )

        if self.context.get("actor_role") == WorkspaceMembership.Rol.ADMIN:
            if (
                self.instance.rol == WorkspaceMembership.Rol.ADMIN
                and self.instance.usuario_id
                != self.context.get("actor_user_id")
            ):
                raise serializers.ValidationError(
                    "Un ADMIN no puede modificar a otro ADMIN."
                )

            if attrs["rol"] == WorkspaceMembership.Rol.ADMIN:
                raise serializers.ValidationError(
                    {"rol": "Un ADMIN no puede asignar el rol ADMIN."}
                )

        return attrs


class WorkspaceOwnershipTransferSerializer(serializers.Serializer):
    username = serializers.SlugRelatedField(
        source="usuario",
        slug_field="username",
        queryset=User.objects.filter(is_active=True),
        error_messages={
            "does_not_exist": "No existe un usuario activo con ese username.",
            "invalid": "Debes enviar un username válido.",
        },
    )

    def validate(self, attrs):
        workspace = self.context.get("workspace")
        if workspace is None:
            raise serializers.ValidationError(
                {"workspace": "No se ha establecido un Workspace válido."}
            )

        membership = WorkspaceMembership.objects.filter(
            workspace=workspace,
            usuario=attrs["usuario"],
        ).first()
        if membership is None:
            raise serializers.ValidationError(
                {
                    "username": (
                        "El usuario debe ser miembro del Workspace "
                        "para recibir la propiedad."
                    )
                }
            )

        if (
            attrs["usuario"].pk == workspace.propietario_id
            and membership.rol == WorkspaceMembership.Rol.OWNER
        ):
            raise serializers.ValidationError(
                {"username": "El usuario ya es propietario del Workspace."}
            )

        attrs["membresia"] = membership
        return attrs
