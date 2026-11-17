
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


class ConsumoRecurso(models.Model):

    producto = models.ForeignKey(
        "productos.Producto",
        on_delete=models.CASCADE,
        related_name="consumos"
    )

    recurso = models.ForeignKey(
        "recursos.Recurso",
        on_delete=models.CASCADE,
        related_name="consumos"
    )

    cantidad_por_unidad = models.DecimalField(
        max_digits=14,
        decimal_places=4
    )

    def __str__(self):
        return (
            f"{self.producto.codigo} - "
            f"{self.recurso.nombre}: "
            f"{self.cantidad_por_unidad}"
        )

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.producto_id and self.recurso_id:
            if self.producto.problema_id != self.recurso.problema_id:
                raise ValidationError(
                    "El producto y el recurso deben pertenecer "
                    "al mismo problema."
                )

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Consumo de recurso"
        verbose_name_plural = "Consumos de recursos"

        constraints = [
            models.UniqueConstraint(
                fields=["producto", "recurso"],
                name="unique_consumo_producto_recurso"
            ),
            models.CheckConstraint(
                condition=models.Q(cantidad_por_unidad__gte=0),
                name="consumo_cantidad_no_negativa"
            )
        ]
