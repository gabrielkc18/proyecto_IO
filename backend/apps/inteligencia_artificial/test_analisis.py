
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

from django.test import TestCase

from apps.problemas.models import Problema
from apps.productos.models import Producto
from apps.recursos.models import Recurso, ConsumoRecurso
from apps.optimizacion.models import Ejecucion
from apps.optimizacion.services.ejecucion import ejecutar_optimizacion

from apps.inteligencia_artificial.models import (
    AnalisisIA,
    SolicitudAnalisisIA,
)
from apps.inteligencia_artificial.services.analisis import generar_analisis
from apps.workspaces.test_utils import crear_workspace_prueba


class GenerarAnalisisTests(TestCase):

    def setUp(self):
        self.usuario, self.workspace = crear_workspace_prueba()
        self.clave_idempotencia = str(uuid4())
        self.problema = Problema.objects.create(
            workspace=self.workspace,
            nombre="Problema análisis IA",
            sentido_objetivo=Problema.SentidoObjetivo.MAXIMIZAR,
            estado=Problema.Estado.LISTO,
        )

        self.producto = Producto.objects.create(
            problema=self.problema,
            codigo="P1",
            nombre="Línea especial",
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

        analisis, replay = generar_analisis(
            ejecucion.id,
            "¿Cuánto debemos producir?",
            consentimiento_confirmado=True,
            solicitante=self.usuario,
            clave_idempotencia=self.clave_idempotencia,
        )

        self.assertFalse(replay)
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
        self.assertNotIn("Problema análisis IA", str(analisis.contexto_enviado))
        self.assertNotIn("Línea especial", str(analisis.contexto_enviado))
        self.assertNotIn("Recurso A", str(analisis.contexto_enviado))
        self.assertNotIn("snapshot_entrada", analisis.contexto_enviado)
        self.assertTrue(analisis.consentimiento_confirmado)
        self.assertIsNotNone(analisis.fecha_consentimiento)
        self.assertLessEqual(
            analisis.fecha_consentimiento,
            analisis.fecha_generacion,
        )
        self.assertEqual(
            analisis.consentimiento_version,
            "ai-disclosure-v1",
        )
        solicitud_enviada = mock_generar.call_args.kwargs["mensajes"][1][
            "content"
        ]
        self.assertNotIn("Línea especial", solicitud_enviada)
        self.assertNotIn("Recurso A", solicitud_enviada)
        self.assertNotIn("Problema análisis IA", solicitud_enviada)
        self.assertNotIn("snapshot_entrada", solicitud_enviada)
        self.assertEqual(AnalisisIA.objects.count(), 1)
        solicitud_ia = SolicitudAnalisisIA.objects.get()
        self.assertEqual(
            solicitud_ia.estado,
            SolicitudAnalisisIA.Estado.COMPLETED,
        )
        self.assertEqual(solicitud_ia.analisis, analisis)
        self.assertEqual(solicitud_ia.solicitante, self.usuario)
        self.assertEqual(solicitud_ia.consentimiento_version, "ai-disclosure-v1")

    @patch(
        "apps.inteligencia_artificial.services.analisis.generar_respuesta"
    )
    def test_sin_consentimiento_no_contacta_al_proveedor(self, mock_generar):
        with self.assertRaisesRegex(ValueError, "consentimiento"):
            generar_analisis(
                99999,
                consentimiento_confirmado=False,
                solicitante=self.usuario,
                clave_idempotencia=self.clave_idempotencia,
            )

        mock_generar.assert_not_called()
        self.assertEqual(AnalisisIA.objects.count(), 0)
        self.assertEqual(SolicitudAnalisisIA.objects.count(), 0)

    def test_ejecucion_inexistente_genera_error(self):
        with self.assertRaises(ValueError):
            generar_analisis(
                99999,
                consentimiento_confirmado=True,
                solicitante=self.usuario,
                clave_idempotencia=self.clave_idempotencia,
            )

        self.assertEqual(AnalisisIA.objects.count(), 0)

    def test_ejecucion_no_terminada_genera_error(self):
        ejecucion = Ejecucion.objects.create(
            problema=self.problema,
            estado_proceso=Ejecucion.EstadoProceso.PENDIENTE,
            solver_nombre="CBC",
            snapshot_entrada={},
        )

        with self.assertRaises(ValueError):
            generar_analisis(
                ejecucion.id,
                consentimiento_confirmado=True,
                solicitante=self.usuario,
                clave_idempotencia=self.clave_idempotencia,
            )

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
            generar_analisis(
                ejecucion.id,
                consentimiento_confirmado=True,
                solicitante=self.usuario,
                clave_idempotencia=self.clave_idempotencia,
            )

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
            generar_analisis(
                ejecucion.id,
                consentimiento_confirmado=True,
                solicitante=self.usuario,
                clave_idempotencia=self.clave_idempotencia,
            )

        self.assertEqual(AnalisisIA.objects.count(), 0)
        solicitud_ia = SolicitudAnalisisIA.objects.get()
        self.assertEqual(
            solicitud_ia.estado,
            SolicitudAnalisisIA.Estado.FAILED,
        )
