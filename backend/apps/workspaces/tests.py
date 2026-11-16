
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Workspace, WorkspaceMembership


User = get_user_model()


class WorkspaceModelTests(TestCase):

    def setUp(self):
        self.usuario = User.objects.create_user(
            username="usuario1",
            password="PruebaSegura123!",
        )

    def test_crear_workspace(self):
        workspace = Workspace.objects.create(
            nombre="Mi espacio",
            propietario=self.usuario,
        )

        self.assertEqual(workspace.nombre, "Mi espacio")
        self.assertEqual(workspace.propietario, self.usuario)

    def test_workspace_tiene_representacion_textual(self):
        workspace = Workspace.objects.create(
            nombre="Mi espacio",
            propietario=self.usuario,
        )

        self.assertEqual(str(workspace), "Mi espacio")


class WorkspaceMembershipModelTests(TestCase):

    def setUp(self):
        self.usuario = User.objects.create_user(
            username="usuario1",
            password="PruebaSegura123!",
        )

        self.workspace = Workspace.objects.create(
            nombre="Mi espacio",
            propietario=self.usuario,
        )

    def test_crear_membresia_owner(self):
        membresia = WorkspaceMembership.objects.create(
            workspace=self.workspace,
            usuario=self.usuario,
            rol=WorkspaceMembership.Rol.OWNER,
        )

        self.assertEqual(
            membresia.rol,
            WorkspaceMembership.Rol.OWNER,
        )

    def test_no_permite_membresias_duplicadas(self):
        WorkspaceMembership.objects.create(
            workspace=self.workspace,
            usuario=self.usuario,
            rol=WorkspaceMembership.Rol.OWNER,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                WorkspaceMembership.objects.create(
                    workspace=self.workspace,
                    usuario=self.usuario,
                    rol=WorkspaceMembership.Rol.ADMIN,
                )

    def test_no_permite_dos_propietarios_en_un_workspace(self):
        otro_usuario = User.objects.create_user(
            username="usuario2",
            password="PruebaSegura123!",
        )

        WorkspaceMembership.objects.create(
            workspace=self.workspace,
            usuario=self.usuario,
            rol=WorkspaceMembership.Rol.OWNER,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                WorkspaceMembership.objects.create(
                    workspace=self.workspace,
                    usuario=otro_usuario,
                    rol=WorkspaceMembership.Rol.OWNER,
                )

    def test_permite_diferentes_roles_en_un_workspace(self):
        otro_usuario = User.objects.create_user(
            username="usuario2",
            password="PruebaSegura123!",
        )

        WorkspaceMembership.objects.create(
            workspace=self.workspace,
            usuario=self.usuario,
            rol=WorkspaceMembership.Rol.OWNER,
        )

        membresia = WorkspaceMembership.objects.create(
            workspace=self.workspace,
            usuario=otro_usuario,
            rol=WorkspaceMembership.Rol.EDITOR,
        )

        self.assertEqual(
            membresia.rol,
            WorkspaceMembership.Rol.EDITOR,
        )
