
from django.test import TestCase
from apps.problemas.models import Problema
from apps.productos.models import Producto
from apps.recursos.models import Recurso
from apps.recursos.serializers import ConsumoRecursoSerializer


class ConsumoRecursoSerializerTests(TestCase):

    def setUp(self):
        self.problema = Problema.objects.create(
            nombre="Problema A"
        )

        self.otro_problema = Problema.objects.create(
            nombre="Problema B"
        )

        self.producto = Producto.objects.create(
            problema=self.problema,
            codigo="P1",
            nombre="Producto 1",
            utilidad_unitaria=80
        )

        self.recurso = Recurso.objects.create(
            problema=self.problema,
            nombre="Materia prima A",
            unidad_medida="kg",
            disponibilidad=3000
        )

        self.recurso_otro_problema = Recurso.objects.create(
            problema=self.otro_problema,
            nombre="Materia prima B",
            unidad_medida="kg",
            disponibilidad=2500
        )

    def test_consumo_valido(self):
        data = {
            "producto": self.producto.id,
            "recurso": self.recurso.id,
            "cantidad_por_unidad": "4.0000"
        }

        serializer = ConsumoRecursoSerializer(data=data)

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors
        )

    def test_rechazar_producto_y_recurso_de_problemas_diferentes(self):
        data = {
            "producto": self.producto.id,
            "recurso": self.recurso_otro_problema.id,
            "cantidad_por_unidad": "4.0000"
        }

        serializer = ConsumoRecursoSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_rechazar_cantidad_negativa(self):
        data = {
            "producto": self.producto.id,
            "recurso": self.recurso.id,
            "cantidad_por_unidad": "-2.0000"
        }

        serializer = ConsumoRecursoSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("cantidad_por_unidad", serializer.errors)
