from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import PerfilCuenta


User = get_user_model()


class RegistroSerializer(serializers.Serializer):
    first_name = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True,
    )
    last_name = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True,
    )
    username = serializers.CharField(
        max_length=User._meta.get_field("username").max_length,
        validators=[UnicodeUsernameValidator()],
    )
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        max_length=128,
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        max_length=128,
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        username = User.normalize_username(attrs["username"])
        attrs["username"] = username
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Las contraseñas no coinciden."}
            )

        candidate = User(username=username, email=attrs["email"])
        try:
            validate_password(attrs["password"], user=candidate)
        except DjangoValidationError as error:
            raise serializers.ValidationError(
                {"password": list(error.messages)}
            ) from error
        return attrs


class PerfilSerializer(serializers.ModelSerializer):
    correo_verificado = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "correo_verificado",
        )
        read_only_fields = ("username", "email", "correo_verificado")

    def get_correo_verificado(self, usuario) -> bool:
        perfil = PerfilCuenta.objects.filter(usuario=usuario).first()
        return True if perfil is None else perfil.correo_verificado


class CambioContrasenaSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        max_length=128,
    )
    new_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        max_length=128,
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        max_length=128,
    )

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError(
                {"current_password": "La contraseña actual no es válida."}
            )
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Las contraseñas no coinciden."}
            )
        try:
            validate_password(attrs["new_password"], user=user)
        except DjangoValidationError as error:
            raise serializers.ValidationError(
                {"new_password": list(error.messages)}
            ) from error
        return attrs


class IdentificadorCuentaSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)


class ConfirmarTokenSerializer(serializers.Serializer):
    uid = serializers.CharField(max_length=64)
    token = serializers.CharField(max_length=128)


class RestablecerContrasenaSerializer(ConfirmarTokenSerializer):
    new_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        max_length=128,
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        max_length=128,
    )

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Las contraseñas no coinciden."}
            )
        return attrs
