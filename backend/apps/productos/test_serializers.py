
from django.test import TestCase

from apps.problemas.models import Problema
from apps.productos.models import Producto
from apps.productos.serializers import ProductoSerializer


class ProductoSerializerTests(TestCase):

    def setUp(self):
        self.problema = Problema.objects.create(
            nombre="Problema de producción"
        )

    def test_crear_producto_valido(self):
        data = {
            "problema": self.problema.id,
            "codigo": "P1",
            "nombre": "Producto 1",
            "utilidad_unitaria": "80.00",
            "activo": True
        }

        serializer = ProductoSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_rechazar_utilidad_negativa(self):
        data = {
            "problema": self.problema.id,
            "codigo": "P2",
            "nombre": "Producto 2",
            "utilidad_unitaria": "-50.00",
            "activo": True
        }

        serializer = ProductoSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("utilidad_unitaria", serializer.errors)

    def test_rechazar_codigo_duplicado(self):
        Producto.objects.create(
            problema=self.problema,
            codigo="P1",
            nombre="Producto existente",
            utilidad_unitaria=80
        )

        data = {
            "problema": self.problema.id,
            "codigo": "P1",
            "nombre": "Producto duplicado",
            "utilidad_unitaria": "100.00",
            "activo": True
        }

        serializer = ProductoSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertTrue(serializer.errors)
