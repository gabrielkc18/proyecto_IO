from django.test import TestCase
from django.core.exceptions import ValidationError

from apps.problemas.models import Problema
from apps.productos.models import Producto
from apps.recursos.models import Recurso
from apps.optimizacion.models import Ejecucion
from .models import ResultadoProducto, ResultadoRecurso
from apps.workspaces.test_utils import crear_workspace_prueba


class ResultadoProductoModelTest(TestCase):

    def setUp(self):
        self.usuario, self.workspace = crear_workspace_prueba()
        self.problema = Problema.objects.create(
            workspace=self.workspace,
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


class ResultadoRecursoTests(TestCase):

    def setUp(self):
        self.usuario, self.workspace = crear_workspace_prueba()
        self.problema = Problema.objects.create(
            workspace=self.workspace,
            nombre="Problema de prueba"
        )

        self.recurso = Recurso.objects.create(
            problema=self.problema,
            nombre="Materia prima A",
            unidad_medida="kg",
            disponibilidad=3000
        )

        self.ejecucion = Ejecucion.objects.create(
            problema=self.problema
        )

    def test_crear_resultado_recurso_correctamente(self):
        resultado = ResultadoRecurso(
            ejecucion=self.ejecucion,
            recurso=self.recurso,
            nombre_recurso=self.recurso.nombre,
            unidad_medida=self.recurso.unidad_medida,
            disponibilidad=3000,
            consumo_total=2500,
            holgura=500,
            estado_uso="CON_HOLGURA"
        )

        resultado.full_clean()
        resultado.save()

        self.assertEqual(resultado.holgura, 500)

    def test_no_permitir_recurso_duplicado_en_ejecucion(self):
        ResultadoRecurso.objects.create(
            ejecucion=self.ejecucion,
            recurso=self.recurso,
            nombre_recurso=self.recurso.nombre,
            unidad_medida=self.recurso.unidad_medida,
            disponibilidad=3000,
            consumo_total=2500,
            holgura=500,
            estado_uso="CON_HOLGURA"
        )

        duplicado = ResultadoRecurso(
            ejecucion=self.ejecucion,
            recurso=self.recurso,
            nombre_recurso=self.recurso.nombre,
            unidad_medida=self.recurso.unidad_medida,
            disponibilidad=3000,
            consumo_total=2500,
            holgura=500,
            estado_uso="CON_HOLGURA"
        )

        with self.assertRaises(ValidationError):
            duplicado.full_clean()

    def test_holgura_no_puede_ser_negativa(self):
        resultado = ResultadoRecurso(
            ejecucion=self.ejecucion,
            recurso=self.recurso,
            nombre_recurso=self.recurso.nombre,
            unidad_medida=self.recurso.unidad_medida,
            disponibilidad=3000,
            consumo_total=3100,
            holgura=-100,
            estado_uso="AGOTADO"
        )

        with self.assertRaises(ValidationError):
            resultado.full_clean()

    def test_estado_uso_debe_ser_valido(self):
        resultado = ResultadoRecurso(
            ejecucion=self.ejecucion,
            recurso=self.recurso,
            nombre_recurso=self.recurso.nombre,
            unidad_medida=self.recurso.unidad_medida,
            disponibilidad=3000,
            consumo_total=3000,
            holgura=0,
            estado_uso="ESTADO_INVALIDO"
        )

        with self.assertRaises(ValidationError):
            resultado.full_clean()
