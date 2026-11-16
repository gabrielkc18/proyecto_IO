
from django.test import TestCase
from django.core.exceptions import ValidationError

from apps.workspaces.test_utils import crear_workspace_prueba, crear_problema_prueba
from apps.problemas.models import Problema
from apps.productos.models import Producto
from apps.recursos.models import Recurso, ConsumoRecurso


class ConsumoRecursoModelTest(TestCase):

    def setUp(self):
        self.usuario, self.workspace = crear_workspace_prueba()

        self.problema_a = crear_problema_prueba(
            self.workspace, nombre="Escenario A"
        )

        self.problema_b = crear_problema_prueba(
            self.workspace, nombre="Escenario B"
        )

        self.producto = Producto.objects.create(
            problema=self.problema_a,
            codigo="P1",
            nombre="Producto 1",
            utilidad_unitaria=80
        )

        self.recurso_a = Recurso.objects.create(
            problema=self.problema_a,
            nombre="Materia prima A",
            unidad_medida="kg",
            disponibilidad=3000
        )

        self.recurso_b = Recurso.objects.create(
            problema=self.problema_b,
            nombre="Materia prima B",
            unidad_medida="kg",
            disponibilidad=2500
        )

    def test_consumo_valido(self):
        consumo = ConsumoRecurso(
            producto=self.producto,
            recurso=self.recurso_a,
            cantidad_por_unidad=4
        )

        consumo.full_clean()

        self.assertEqual(
            consumo.cantidad_por_unidad,
            4
        )

    def test_producto_y_recurso_deben_pertenecer_al_mismo_problema(self):
        consumo = ConsumoRecurso(
            producto=self.producto,
            recurso=self.recurso_b,
            cantidad_por_unidad=4
        )

        with self.assertRaises(ValidationError):
            consumo.full_clean()

    def test_consumo_no_puede_ser_negativo(self):
        consumo = ConsumoRecurso(
            producto=self.producto,
            recurso=self.recurso_a,
            cantidad_por_unidad=-5
        )

        with self.assertRaises(ValidationError):
            consumo.full_clean()

    def test_no_permite_consumos_duplicados(self):
        ConsumoRecurso.objects.create(
            producto=self.producto,
            recurso=self.recurso_a,
            cantidad_por_unidad=4
        )

        duplicado = ConsumoRecurso(
            producto=self.producto,
            recurso=self.recurso_a,
            cantidad_por_unidad=6
        )

        with self.assertRaises(ValidationError):
            duplicado.full_clean()
