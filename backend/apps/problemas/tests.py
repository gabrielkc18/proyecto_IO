
from django.test import TestCase
from django.core.exceptions import ValidationError

from apps.problemas.models import Problema
from apps.workspaces.test_utils import (
    crear_workspace_prueba,
    crear_problema_prueba,
)


class ProblemaModelTest(TestCase):

    def setUp(self):
        self.usuario, self.workspace = crear_workspace_prueba()

    def test_crear_problema_correctamente(self):
        problema = crear_problema_prueba(
            self.workspace,
            nombre="Producción noviembre",
            descripcion="Escenario de producción",
        )

        self.assertEqual(problema.nombre, "Producción noviembre")
        self.assertEqual(problema.estado, "BORRADOR")
        self.assertEqual(problema.sentido_objetivo, "MAXIMIZAR")
        self.assertIsNotNone(problema.fecha_creacion)
        self.assertEqual(problema.workspace, self.workspace)

    def test_nombre_debe_ser_unico_en_el_mismo_workspace(self):
        crear_problema_prueba(
            self.workspace,
            nombre="Producción noviembre",
        )

        duplicado = Problema(
            workspace=self.workspace,
            nombre="Producción noviembre",
        )

        with self.assertRaises(ValidationError):
            duplicado.full_clean()

    def test_nombre_puede_repetirse_en_otro_workspace(self):
        _, otro_workspace = crear_workspace_prueba(
            nombre="Otro workspace",
        )

        crear_problema_prueba(
            self.workspace,
            nombre="Producción noviembre",
        )

        otro_problema = Problema(
            workspace=otro_workspace,
            nombre="Producción noviembre",
        )

        otro_problema.full_clean()

    def test_sentido_objetivo_debe_ser_valido(self):
        problema = Problema(
            workspace=self.workspace,
            nombre="Producción diciembre",
            sentido_objetivo="ALEATORIO",
        )

        with self.assertRaises(ValidationError):
            problema.full_clean()

    def test_estado_debe_ser_valido(self):
        problema = Problema(
            workspace=self.workspace,
            nombre="Producción enero",
            estado="INEXISTENTE",
        )

        with self.assertRaises(ValidationError):
            problema.full_clean()
