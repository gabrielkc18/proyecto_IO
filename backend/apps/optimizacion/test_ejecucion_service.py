
from decimal import Decimal

from django.test import TestCase

from apps.problemas.models import Problema
from apps.productos.models import Producto
from apps.recursos.models import Recurso, ConsumoRecurso
from apps.optimizacion.models import Ejecucion
from apps.resultados.models import ResultadoProducto, ResultadoRecurso
from apps.optimizacion.services.ejecucion import ejecutar_optimizacion
from apps.workspaces.test_utils import crear_workspace_prueba


class EjecucionServiceTests(TestCase):

    def setUp(self):
        self.usuario, self.workspace = crear_workspace_prueba()
        self.problema = Problema.objects.create(
            workspace=self.workspace,
            nombre="Problema de prueba",
            sentido_objetivo=Problema.SentidoObjetivo.MAXIMIZAR,
            estado=Problema.Estado.LISTO,
        )

        self.producto = Producto.objects.create(
            problema=self.problema,
            codigo="P1",
            nombre="Producto 1",
            utilidad_unitaria=Decimal("5.00"),
        )

        self.recurso = Recurso.objects.create(
            problema=self.problema,
            nombre="Recurso A",
            unidad_medida="kg",
            disponibilidad=Decimal("10.00"),
        )

        ConsumoRecurso.objects.create(
            producto=self.producto,
            recurso=self.recurso,
            cantidad_por_unidad=Decimal("2.0000"),
        )

    def test_ejecucion_optima_guarda_resultados(self):
        ejecucion = ejecutar_optimizacion(self.problema.id)

        self.assertEqual(
            ejecucion.estado_proceso,
            Ejecucion.EstadoProceso.TERMINADO,
        )
        self.assertEqual(
            ejecucion.estado_solver,
            Ejecucion.EstadoSolver.OPTIMAL,
        )
        self.assertEqual(ejecucion.utilidad_total, Decimal("25.00"))

        resultado_producto = ResultadoProducto.objects.get(
            ejecucion=ejecucion
        )

        self.assertEqual(resultado_producto.cantidad, 5)
        self.assertEqual(
            resultado_producto.utilidad_aportada,
            Decimal("25.00"),
        )

        resultado_recurso = ResultadoRecurso.objects.get(
            ejecucion=ejecucion
        )

        self.assertEqual(
            resultado_recurso.consumo_total,
            Decimal("10.00"),
        )
        self.assertEqual(
            resultado_recurso.holgura,
            Decimal("0.00"),
        )
        self.assertEqual(
            resultado_recurso.estado_uso,
            ResultadoRecurso.EstadoUso.AGOTADO,
        )

    def test_problema_no_listo_no_crea_ejecucion(self):
        self.problema.estado = Problema.Estado.BORRADOR
        self.problema.save()

        with self.assertRaises(ValueError):
            ejecutar_optimizacion(self.problema.id)

        self.assertEqual(Ejecucion.objects.count(), 0)

    def test_sin_productos_activos_no_crea_ejecucion(self):
        self.producto.activo = False
        self.producto.save()

        with self.assertRaises(ValueError):
            ejecutar_optimizacion(self.problema.id)

        self.assertEqual(Ejecucion.objects.count(), 0)

    def test_error_del_solver_se_registra_en_ejecucion(self):
        from unittest.mock import patch

        with patch(
            "apps.optimizacion.services.ejecucion.resolver_problema",
            side_effect=RuntimeError("Error simulado del solver"),
        ):
            ejecucion = ejecutar_optimizacion(self.problema.id)

        self.assertEqual(
            ejecucion.estado_proceso,
            Ejecucion.EstadoProceso.ERROR,
        )
        self.assertIn(
            "Error simulado del solver",
            ejecucion.mensaje_error,
        )
        self.assertIsNotNone(ejecucion.fecha_fin)
