
from django.db import models


class Ejecucion(models.Model):

    class EstadoProceso(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        EN_CURSO = "EN_CURSO", "En curso"
        TERMINADO = "TERMINADO", "Terminado"
        ERROR = "ERROR", "Error"

    class EstadoSolver(models.TextChoices):
        OPTIMAL = "Optimal", "Óptimo"
        INFEASIBLE = "Infeasible", "Infactible"
        UNBOUNDED = "Unbounded", "No acotado"
        NOT_SOLVED = "Not Solved", "No resuelto"
        UNDEFINED = "Undefined", "Indefinido"

    problema = models.ForeignKey(
        "problemas.Problema",
        on_delete=models.PROTECT,
        related_name="ejecuciones"
    )

    fecha_inicio = models.DateTimeField(
        auto_now_add=True
    )

    fecha_fin = models.DateTimeField(
        null=True,
        blank=True
    )

    estado_proceso = models.CharField(
        max_length=12,
        choices=EstadoProceso.choices,
        default=EstadoProceso.PENDIENTE
    )

    estado_solver = models.CharField(
        max_length=20,
        choices=EstadoSolver.choices,
        null=True,
        blank=True
    )

    utilidad_total = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        null=True,
        blank=True
    )

    solver_nombre = models.CharField(
        max_length=100,
        blank=True
    )

    mensaje_error = models.TextField(
        blank=True
    )

    snapshot_entrada = models.JSONField(
        default=dict
    )

    def __str__(self):
        return f"Ejecución {self.pk} - {self.problema.nombre}"

    class Meta:
        verbose_name = "Ejecución"
        verbose_name_plural = "Ejecuciones"
        ordering = ["-fecha_inicio"]
