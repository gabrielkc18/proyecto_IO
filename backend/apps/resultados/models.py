
from django.db import models


class ResultadoProducto(models.Model):

    ejecucion = models.ForeignKey(
        "optimizacion.Ejecucion",
        on_delete=models.PROTECT,
        related_name="resultados_productos"
    )

    producto = models.ForeignKey(
        "productos.Producto",
        on_delete=models.PROTECT,
        related_name="resultados"
    )

    nombre_producto = models.CharField(
        max_length=150
    )

    utilidad_unitaria = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    cantidad = models.PositiveIntegerField()

    utilidad_aportada = models.DecimalField(
        max_digits=16,
        decimal_places=2
    )

    def __str__(self):
        return f"{self.nombre_producto}: {self.cantidad} unidades"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["ejecucion", "producto"],
                name="unique_resultado_producto_por_ejecucion"
            ),
            models.CheckConstraint(
                condition=models.Q(utilidad_aportada__gte=0),
                name="resultado_utilidad_aportada_no_negativa"
            ),
        ]


class ResultadoRecurso(models.Model):

    class EstadoUso(models.TextChoices):
        AGOTADO = "AGOTADO", "Agotado"
        CON_HOLGURA = "CON_HOLGURA", "Con holgura"

    ejecucion = models.ForeignKey(
        "optimizacion.Ejecucion",
        on_delete=models.PROTECT,
        related_name="resultados_recursos"
    )

    recurso = models.ForeignKey(
        "recursos.Recurso",
        on_delete=models.PROTECT,
        related_name="resultados"
    )

    nombre_recurso = models.CharField(
        max_length=100
    )

    unidad_medida = models.CharField(
        max_length=30
    )

    disponibilidad = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )

    consumo_total = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )

    holgura = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )

    estado_uso = models.CharField(
        max_length=15,
        choices=EstadoUso.choices
    )

    def __str__(self):
        return f"{self.nombre_recurso}: {self.estado_uso}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["ejecucion", "recurso"],
                name="unique_resultado_recurso_por_ejecucion"
            ),
            models.CheckConstraint(
                condition=models.Q(holgura__gte=0),
                name="resultado_recurso_holgura_no_negativa"
            ),
        ]                                                                       