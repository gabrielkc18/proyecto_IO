
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

    def __str__(self):
        return f"Análisis {self.pk} - Ejecución {self.ejecucion_id}"

    class Meta:
        verbose_name = "Análisis de IA"
        verbose_name_plural = "Análisis de IA"
        ordering = ["-fecha_generacion"]
