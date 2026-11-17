from datetime import timedelta
from io import StringIO
from uuid import uuid4

from django.core.management import call_command, CommandError
from django.test import TestCase
from django.utils import timezone

from apps.inteligencia_artificial.models import SolicitudAnalisisIA
from apps.optimizacion.models import Ejecucion
from apps.problemas.models import Problema
from apps.workspaces.test_utils import crear_workspace_prueba


class RecoverStaleAIRequestsTests(TestCase):
    def setUp(self):
        self.usuario, workspace = crear_workspace_prueba()
        problema = Problema.objects.create(
            workspace=workspace,
            nombre="Problema solicitudes IA",
            sentido_objetivo=Problema.SentidoObjetivo.MAXIMIZAR,
            estado=Problema.Estado.LISTO,
        )
        self.ejecucion = Ejecucion.objects.create(
            problema=problema,
            estado_proceso=Ejecucion.EstadoProceso.TERMINADO,
            estado_solver=Ejecucion.EstadoSolver.OPTIMAL,
            solver_nombre="CBC",
            snapshot_entrada={},
        )

    def crear_solicitud(self, minutos_antiguedad):
        solicitud = SolicitudAnalisisIA.objects.create(
            ejecucion=self.ejecucion,
            solicitante=self.usuario,
            clave_idempotencia=str(uuid4()),
            huella_solicitud="a" * 64,
            fecha_consentimiento=timezone.now(),
            consentimiento_version="ai-disclosure-v1",
        )
        SolicitudAnalisisIA.objects.filter(pk=solicitud.pk).update(
            fecha_creacion=timezone.now() - timedelta(
                minutes=minutos_antiguedad,
            ),
        )
        return solicitud

    def test_recupera_solo_solicitudes_que_superan_el_umbral(self):
        antigua = self.crear_solicitud(minutos_antiguedad=60)
        reciente = self.crear_solicitud(minutos_antiguedad=5)

        call_command(
            "recover_stale_ai_requests",
            older_than_minutes=30,
            stdout=StringIO(),
        )

        antigua.refresh_from_db()
        reciente.refresh_from_db()
        self.assertEqual(
            antigua.estado,
            SolicitudAnalisisIA.Estado.FAILED,
        )
        self.assertEqual(
            reciente.estado,
            SolicitudAnalisisIA.Estado.PROCESSING,
        )

    def test_dry_run_no_modifica_solicitudes(self):
        solicitud = self.crear_solicitud(minutos_antiguedad=60)

        call_command(
            "recover_stale_ai_requests",
            older_than_minutes=30,
            dry_run=True,
            stdout=StringIO(),
        )

        solicitud.refresh_from_db()
        self.assertEqual(
            solicitud.estado,
            SolicitudAnalisisIA.Estado.PROCESSING,
        )

    def test_rechaza_un_umbral_no_positivo(self):
        with self.assertRaises(CommandError):
            call_command(
                "recover_stale_ai_requests",
                older_than_minutes=0,
                stdout=StringIO(),
            )
