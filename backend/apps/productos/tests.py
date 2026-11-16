
from django.test import TestCase
from django.core.exceptions import ValidationError

from apps.problemas.models import Problema
from apps.productos.models import Producto


class ProductoModelTest(TestCase):

    def setUp(self):
        self.problema = Problema.objects.create(
            nombre="Producción noviembre"
        )

    def test_crear_producto_correctamente(self):
        producto = Producto.objects.create(
            problema=self.problema,
            codigo="P1",
            nombre="Producto 1",
            utilidad_unitaria=80
        )

        self.assertEqual(producto.codigo, "P1")
        self.assertEqual(producto.utilidad_unitaria, 80)
        self.assertTrue(producto.activo)

    def test_codigo_unico_dentro_del_problema(self):
        Producto.objects.create(
            problema=self.problema,
            codigo="P1",
            nombre="Producto 1",
            utilidad_unitaria=80
        )

        duplicado = Producto(
            problema=self.problema,
            codigo="P1",
            nombre="Producto duplicado",
            utilidad_unitaria=100
        )

        with self.assertRaises(ValidationError):
            duplicado.full_clean()

    def test_mismo_codigo_permitido_en_otro_problema(self):
        otro_problema = Problema.objects.create(
            nombre="Producción diciembre"
        )

        Producto.objects.create(
            problema=self.problema,
            codigo="P1",
            nombre="Producto 1",
            utilidad_unitaria=80
        )

        producto = Producto(
            problema=otro_problema,
            codigo="P1",
            nombre="Producto 1",
            utilidad_unitaria=90
        )

        producto.full_clean()

    def test_utilidad_no_puede_ser_negativa(self):
        producto = Producto(
            problema=self.problema,
            codigo="P2",
            nombre="Producto 2",
            utilidad_unitaria=-50
        )

        with self.assertRaises(ValidationError):
            producto.full_clean()
