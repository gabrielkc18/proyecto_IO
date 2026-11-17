from uuid import UUID

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
            "consentimiento_confirmado",
            "fecha_consentimiento",
            "consentimiento_version",
        ]
        read_only_fields = fields


class GenerarAnalisisSerializer(serializers.Serializer):

    pregunta = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=5000,
    )
    consentimiento_confirmado = serializers.BooleanField(
        required=True,
        help_text=(
            "Autoriza a enviar a Groq el contexto de la ejecución y la "
            "pregunta proporcionada."
        ),
    )

    def validate_consentimiento_confirmado(self, value):
        if not value:
            raise serializers.ValidationError(
                "Debes autorizar el envío de datos a Groq para generar el análisis."
            )
        return value

    def validate(self, attrs):
        clave = self.context.get("idempotency_key")
        try:
            attrs["idempotency_key"] = str(UUID(clave))
        except (AttributeError, TypeError, ValueError) as error:
            raise serializers.ValidationError(
                {
                    "Idempotency-Key": (
                        "Envía una clave UUID en el encabezado Idempotency-Key."
                    )
                }
            ) from error
        return attrs
