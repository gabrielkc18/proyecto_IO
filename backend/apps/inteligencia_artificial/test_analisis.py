
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from apps.problemas.models import Problema
from apps.productos.models import Producto
from apps.recursos.models import Recurso, ConsumoRecurso
from apps.optimizacion.models import Ejecucion
from apps.optimizacion.services.ejecucion import ejecutar_optimizacion

from apps.inteligencia_artificial.models import AnalisisIA
from apps.inteligencia_artificial.services.analisis import generar_analisis


class GenerarAnalisisTests(TestCase):

    def setUp(self):
        self.problema = Problema.objects.create(
            nombre="Problema análisis IA",
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

    @patch(
        "apps.inteligencia_artificial.services.analisis.generar_respuesta"
    )
    def test_genera_y_guarda_analisis(self, mock_generar):
        mock_generar.return_value = {
            "contenido": "La producción óptima es de 5 unidades.",
            "modelo": "openai/gpt-oss-120b",
        }

        ejecucion = ejecutar_optimizacion(self.problema.id)

        analisis = generar_analisis(
            ejecucion.id,
            "¿Cuánto debemos producir?",
        )

        self.assertIsInstance(analisis, AnalisisIA)
        self.assertEqual(analisis.ejecucion_id, ejecucion.id)
        self.assertEqual(
            analisis.contenido,
            "La producción óptima es de 5 unidades.",
        )
        self.assertEqual(
            analisis.modelo_ia,
            "openai/gpt-oss-120b",
        )
        self.assertEqual(
            analisis.pregunta,
            "¿Cuánto debemos producir?",
        )
        self.assertIn("productos", analisis.contexto_enviado)
        self.assertEqual(AnalisisIA.objects.count(), 1)

    def test_ejecucion_inexistente_genera_error(self):
        with self.assertRaises(ValueError):
            generar_analisis(99999)

        self.assertEqual(AnalisisIA.objects.count(), 0)

    def test_ejecucion_no_terminada_genera_error(self):
        ejecucion = Ejecucion.objects.create(
            problema=self.problema,
            estado_proceso=Ejecucion.EstadoProceso.PENDIENTE,
            solver_nombre="CBC",
            snapshot_entrada={},
        )

        with self.assertRaises(ValueError):
            generar_analisis(ejecucion.id)

        self.assertEqual(AnalisisIA.objects.count(), 0)

    def test_ejecucion_no_optima_genera_error(self):
        ejecucion = Ejecucion.objects.create(
            problema=self.problema,
            estado_proceso=Ejecucion.EstadoProceso.TERMINADO,
            estado_solver=Ejecucion.EstadoSolver.INFEASIBLE,
            solver_nombre="CBC",
            snapshot_entrada={},
        )

        with self.assertRaises(ValueError):
            generar_analisis(ejecucion.id)

        self.assertEqual(AnalisisIA.objects.count(), 0)

    @patch(
        "apps.inteligencia_artificial.services.analisis.generar_respuesta"
    )
    def test_error_del_proveedor_no_guarda_analisis(self, mock_generar):
        mock_generar.side_effect = RuntimeError(
            "Error de conexión con Groq"
        )

        ejecucion = ejecutar_optimizacion(self.problema.id)

        with self.assertRaises(RuntimeError):
            generar_analisis(ejecucion.id)

        self.assertEqual(AnalisisIA.objects.count(), 0)
