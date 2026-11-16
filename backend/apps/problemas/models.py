
from django.db import models


class Problema(models.Model):

    class SentidoObjetivo(models.TextChoices):
        MAXIMIZAR = "MAXIMIZAR", "Maximizar"
        MINIMIZAR = "MINIMIZAR", "Minimizar"

    class Estado(models.TextChoices):
        BORRADOR = "BORRADOR", "Borrador"
        LISTO = "LISTO", "Listo"
        ARCHIVADO = "ARCHIVADO", "Archivado"

    nombre = models.CharField(
        max_length=150,
        unique=True
    )

    descripcion = models.TextField(
        blank=True
    )

    sentido_objetivo = models.CharField(
        max_length=10,
        choices=SentidoObjetivo.choices,
        default=SentidoObjetivo.MAXIMIZAR
    )

    estado = models.CharField(
        max_length=10,
        choices=Estado.choices,
        default=Estado.BORRADOR
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Problema"
        verbose_name_plural = "Problemas"
        ordering = ["-fecha_creacion"]
