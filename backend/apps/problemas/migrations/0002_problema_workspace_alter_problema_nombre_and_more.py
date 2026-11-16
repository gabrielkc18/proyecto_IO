
from django.db import migrations, models
import django.db.models.deletion


def crear_workspaces_personales(apps, schema_editor):
    Workspace = apps.get_model("workspaces", "Workspace")
    WorkspaceMembership = apps.get_model(
        "workspaces",
        "WorkspaceMembership",
    )
    Problema = apps.get_model("problemas", "Problema")
    User = apps.get_model("auth", "User")

    db_alias = schema_editor.connection.alias

    usuarios = list(
        User.objects.using(db_alias).all().order_by("pk")
    )

    problemas_sin_workspace = Problema.objects.using(
        db_alias
    ).filter(workspace__isnull=True)

    if problemas_sin_workspace.exists() and len(usuarios) != 1:
        raise RuntimeError(
            "No se pueden asignar los problemas históricos "
            "automáticamente: se requiere identificar a sus "
            "propietarios antes de continuar."
        )

    workspaces_por_usuario = {}

    for usuario in usuarios:
        nombre_workspace = (
            f"Espacio personal de {usuario.username}"
        )

        workspace, _ = Workspace.objects.using(
            db_alias
        ).get_or_create(
            propietario_id=usuario.pk,
            nombre=nombre_workspace,
        )

        WorkspaceMembership.objects.using(
            db_alias
        ).get_or_create(
            workspace_id=workspace.pk,
            usuario_id=usuario.pk,
            defaults={"rol": "OWNER"},
        )

        workspaces_por_usuario[usuario.pk] = workspace.pk

    if problemas_sin_workspace.exists():
        usuario = usuarios[0]
        workspace_id = workspaces_por_usuario[usuario.pk]

        problemas_sin_workspace.update(
            workspace_id=workspace_id
        )


class Migration(migrations.Migration):

    dependencies = [
        ("problemas", "0001_initial"),
        ("workspaces", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.AddField(
            model_name="problema",
            name="workspace",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="problemas",
                to="workspaces.workspace",
            ),
        ),

        migrations.AlterField(
            model_name="problema",
            name="nombre",
            field=models.CharField(max_length=150),
        ),

        migrations.RunPython(
            crear_workspaces_personales,
            migrations.RunPython.noop,
        ),

        migrations.AlterField(
            model_name="problema",
            name="workspace",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="problemas",
                to="workspaces.workspace",
            ),
        ),

        migrations.AddConstraint(
            model_name="problema",
            constraint=models.UniqueConstraint(
                fields=("workspace", "nombre"),
                name="unique_problema_por_workspace",
            ),
        ),
    ]
