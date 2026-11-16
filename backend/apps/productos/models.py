
from django.db import models


class Producto(models.Model):

    problema = models.ForeignKey(
        "problemas.Problema",
        on_delete=models.CASCADE,
        related_name="productos"
    )

    codigo = models.CharField(
        max_length=20
    )

    nombre = models.CharField(
        max_length=150
    )

    descripcion = models.TextField(
        blank=True
    )

    utilidad_unitaria = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    activo = models.BooleanField(
        default=True
    )

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["codigo"]

        constraints = [
            models.UniqueConstraint(
                fields=["problema", "codigo"],
                name="unique_producto_por_problema"
            ),
            models.CheckConstraint(
                condition=models.Q(utilidad_unitaria__gte=0),
                name="producto_utilidad_no_negativa"
            )
        ]