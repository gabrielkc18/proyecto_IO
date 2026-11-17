
from django.conf import settings
from django.db import models


class AnalisisIA(models.Model):

    ejecucion = models.ForeignKey(
        "optimizacion.Ejecucion",
        on_delete=models.PROTECT,
        related_name="analisis_ia"
    )

    tipo_analisis = models.CharField(
        max_length=30
    )

    pregunta = models.TextField(
        blank=True
    )

    contenido = models.TextField()

    modelo_ia = models.CharField(
        max_length=100
    )

    fecha_generacion = models.DateTimeField(
        auto_now_add=True
    )

    contexto_enviado = models.JSONField(
        default=dict
    )

    consentimiento_confirmado = models.BooleanField(
        null=True,
        blank=True,
        default=None,
    )

    fecha_consentimiento = models.DateTimeField(
        null=True,
        blank=True,
    )

    consentimiento_version = models.CharField(
        max_length=40,
        null=True,
        blank=True,
    )

    solicitado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="analisis_ia_solicitados",
    )

    def __str__(self):
        return f"Análisis {self.pk} - Ejecución {self.ejecucion_id}"

    class Meta:
        verbose_name = "Análisis de IA"
        verbose_name_plural = "Análisis de IA"
        ordering = ["-fecha_generacion"]


class SolicitudAnalisisIA(models.Model):
    class Estado(models.TextChoices):
        PROCESSING = "PROCESSING", "En proceso"
        COMPLETED = "COMPLETED", "Completada"
        FAILED = "FAILED", "Fallida"

    ejecucion = models.ForeignKey(
        "optimizacion.Ejecucion",
        on_delete=models.CASCADE,
        related_name="solicitudes_ia",
    )
    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="solicitudes_analisis_ia",
    )
    clave_idempotencia = models.CharField(max_length=36)
    huella_solicitud = models.CharField(max_length=64)
    estado = models.CharField(
        max_length=10,
        choices=Estado.choices,
        default=Estado.PROCESSING,
    )
    consentimiento_confirmado = models.BooleanField(default=True)
    fecha_consentimiento = models.DateTimeField()
    consentimiento_version = models.CharField(max_length=40)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    analisis = models.OneToOneField(
        AnalisisIA,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="solicitud_idempotente",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("solicitante", "clave_idempotencia"),
                name="unique_ai_requester_idempotency_key",
            ),
        ]
