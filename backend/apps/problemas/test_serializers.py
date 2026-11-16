
from django.test import TestCase

from apps.problemas.models import Problema
from apps.problemas.serializers import ProblemaSerializer
from apps.workspaces.test_utils import (
    crear_workspace_prueba,
    crear_problema_prueba,
)


class ProblemaSerializerTests(TestCase):

    def setUp(self):
        self.usuario, self.workspace = crear_workspace_prueba()
        self.context = {"workspace": self.workspace}

    def test_crear_problema_valido(self):
        data = {
            "nombre": "Producción industrial",
            "descripcion": "Optimización de producción",
            "sentido_objetivo": "MAXIMIZAR",
            "estado": "BORRADOR",
        }

        serializer = ProblemaSerializer(
            data=data,
            context=self.context,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_nombre_obligatorio(self):
        data = {
            "descripcion": "Problema sin nombre",
            "sentido_objetivo": "MAXIMIZAR",
            "estado": "BORRADOR",
        }

        serializer = ProblemaSerializer(
            data=data,
            context=self.context,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("nombre", serializer.errors)

    def test_nombre_unico_en_workspace(self):
        crear_problema_prueba(
            self.workspace,
            nombre="Producción industrial",
        )

        data = {
            "nombre": "Producción industrial",
            "sentido_objetivo": "MAXIMIZAR",
            "estado": "BORRADOR",
        }

        serializer = ProblemaSerializer(
            data=data,
            context=self.context,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("nombre", serializer.errors)

    def test_nombre_repetido_en_otro_workspace_es_valido(self):
        _, otro_workspace = crear_workspace_prueba(
            nombre="Workspace secundario",
        )

        crear_problema_prueba(
            self.workspace,
            nombre="Producción industrial",
        )

        serializer = ProblemaSerializer(
            data={
                "nombre": "Producción industrial",
                "sentido_objetivo": "MAXIMIZAR",
                "estado": "BORRADOR",
            },
            context={"workspace": otro_workspace},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_workspace_no_es_un_campo_editable(self):
        serializer = ProblemaSerializer()

        self.assertNotIn("workspace", serializer.fields)
