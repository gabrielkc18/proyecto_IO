
from django.test import TestCase
from django.core.exceptions import ValidationError

from apps.problemas.models import Problema
from apps.productos.models import Producto
from apps.optimizacion.models import Ejecucion
from apps.resultados.models import ResultadoProducto


class ResultadoProductoModelTest(TestCase):

    def setUp(self):
        self.problema = Problema.objects.create(
            nombre="Producción noviembre"
        )

        self.producto = Producto.objects.create(
            problema=self.problema,
            codigo="P1",
            nombre="Producto 1",
            utilidad_unitaria=80
        )

        self.ejecucion = Ejecucion.objects.create(
            problema=self.problema
        )

    def test_crear_resultado_correctamente(self):
        resultado = ResultadoProducto.objects.create(
            ejecucion=self.ejecucion,
            producto=self.producto,
            nombre_producto="Producto 1",
            utilidad_unitaria=80,
            cantidad=150,
            utilidad_aportada=12000
        )

        self.assertEqual(resultado.cantidad, 150)
        self.assertEqual(resultado.utilidad_aportada, 12000)

    def test_no_permite_resultados_duplicados(self):
        ResultadoProducto.objects.create(
            ejecucion=self.ejecucion,
            producto=self.producto,
            nombre_producto="Producto 1",
            utilidad_unitaria=80,
            cantidad=150,
            utilidad_aportada=12000
        )

        duplicado = ResultadoProducto(
            ejecucion=self.ejecucion,
            producto=self.producto,
            nombre_producto="Producto 1",
            utilidad_unitaria=80,
            cantidad=100,
            utilidad_aportada=8000
        )

        with self.assertRaises(ValidationError):
            duplicado.full_clean()

    def test_cantidad_no_puede_ser_negativa(self):
        resultado = ResultadoProducto(
            ejecucion=self.ejecucion,
            producto=self.producto,
            nombre_producto="Producto 1",
            utilidad_unitaria=80,
            cantidad=-10,
            utilidad_aportada=-800
        )

        with self.assertRaises(ValidationError):
            resultado.full_clean()

    def test_utilidad_aportada_no_puede_ser_negativa(self):
        resultado = ResultadoProducto(
            ejecucion=self.ejecucion,
            producto=self.producto,
            nombre_producto="Producto 1",
            utilidad_unitaria=80,
            cantidad=10,
            utilidad_aportada=-800
        )

        with self.assertRaises(ValidationError):
            resultado.full_clean()
