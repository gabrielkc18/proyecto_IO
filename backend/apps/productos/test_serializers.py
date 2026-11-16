from django.test import TestCase

from apps.productos.models import Producto
from apps.productos.serializers import ProductoSerializer
from apps.workspaces.test_utils import (
    crear_workspace_prueba,
    crear_problema_prueba,
)


class ProductoSerializerTests(TestCase):

    def setUp(self):
        self.usuario, self.workspace = crear_workspace_prueba()

        self.problema = crear_problema_prueba(
            self.workspace,
            nombre="Problema de producción",
        )

        self.context = {"workspace": self.workspace}

    def test_crear_producto_valido(self):
        data = {
            "problema": self.problema.id,
            "codigo": "P1",
            "nombre": "Producto 1",
            "utilidad_unitaria": "80.00",
            "activo": True,
        }

        serializer = ProductoSerializer(
            data=data,
            context=self.context,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_rechazar_utilidad_negativa(self):
        data = {
            "problema": self.problema.id,
            "codigo": "P2",
            "nombre": "Producto 2",
            "utilidad_unitaria": "-50.00",
            "activo": True,
        }

        serializer = ProductoSerializer(
            data=data,
            context=self.context,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("utilidad_unitaria", serializer.errors)

    def test_rechazar_codigo_duplicado(self):
        Producto.objects.create(
            problema=self.problema,
            codigo="P1",
            nombre="Producto existente",
            utilidad_unitaria=80,
        )

        data = {
            "problema": self.problema.id,
            "codigo": "P1",
            "nombre": "Producto duplicado",
            "utilidad_unitaria": "100.00",
            "activo": True,
        }

        serializer = ProductoSerializer(
            data=data,
            context=self.context,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("codigo", serializer.errors)

    def test_rechazar_problema_de_otro_workspace(self):
        _, otro_workspace = crear_workspace_prueba(
            nombre="Workspace externo",
        )

        otro_problema = crear_problema_prueba(
            otro_workspace,
            nombre="Problema externo",
        )

        data = {
            "problema": otro_problema.id,
            "codigo": "P3",
            "nombre": "Producto externo",
            "utilidad_unitaria": "80.00",
            "activo": True,
        }

        serializer = ProductoSerializer(
            data=data,
            context=self.context,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("problema", serializer.errors)

    def test_rechazar_serializer_sin_workspace(self):
        data = {
            "problema": self.problema.id,
            "codigo": "P4",
            "nombre": "Producto sin contexto",
            "utilidad_unitaria": "80.00",
        }

        serializer = ProductoSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("problema", serializer.errors)
