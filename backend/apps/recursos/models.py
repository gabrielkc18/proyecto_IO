
from django.db import models
from django.db.models import Q


class Recurso(models.Model):

    problema = models.ForeignKey(
        "problemas.Problema",
        on_delete=models.CASCADE,
        related_name="recursos"
    )

    nombre = models.CharField(
        max_length=100
    )

    unidad_medida = models.CharField(
        max_length=30
    )

    disponibilidad = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )

    activo = models.BooleanField(
        default=True
    )

    def __str__(self):
        return f"{self.nombre} ({self.unidad_medida})"

    class Meta:
        verbose_name = "Recurso"
        verbose_name_plural = "Recursos"
        ordering = ["nombre"]

        constraints = [
            models.UniqueConstraint(
                fields=["problema", "nombre"],
                name="unique_recurso_por_problema"
            ),
            models.CheckConstraint(
                condition=Q(disponibilidad__gte=0),
                name="recurso_disponibilidad_no_negativa"
            )
        ]
