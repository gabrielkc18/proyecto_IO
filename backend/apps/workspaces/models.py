
from django.conf import settings
from django.db import models


class Workspace(models.Model):

    nombre = models.CharField(max_length=150)

    propietario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="workspaces_propietario",
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Workspace"
        verbose_name_plural = "Workspaces"
        ordering = ["nombre"]


class WorkspaceMembership(models.Model):

    class Rol(models.TextChoices):
        OWNER = "OWNER", "Propietario"
        ADMIN = "ADMIN", "Administrador"
        EDITOR = "EDITOR", "Editor"
        VIEWER = "VIEWER", "Visualizador"

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.PROTECT,
        related_name="membresias",
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="membresias_workspace",
    )

    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.usuario} - "
            f"{self.workspace} ({self.rol})"
        )

    class Meta:
        verbose_name = "Membresía de Workspace"
        verbose_name_plural = "Membresías de Workspaces"

        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "usuario"],
                name="unique_usuario_por_workspace",
            ),
            models.UniqueConstraint(
                fields=["workspace"],
                condition=models.Q(rol="OWNER"),
                name="unique_owner_por_workspace",
            ),
        ]
