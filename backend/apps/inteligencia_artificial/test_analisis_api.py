from django.contrib.auth import get_user_model

from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

from django.core.cache import cache
from rest_framework.test import APITestCase
from rest_framework import status

from apps.problemas.models import Problema
from apps.productos.models import Producto
from apps.recursos.models import Recurso, ConsumoRecurso
from apps.optimizacion.services.ejecucion import ejecutar_optimizacion
from apps.inteligencia_artificial.models import (
    AnalisisIA,
    SolicitudAnalisisIA,
)
from apps.workspaces.test_utils import crear_workspace_prueba


class GenerarAnalisisAPITests(APITestCase):

    def setUp(self):
        cache.clear()
        self.idempotency_key = str(uuid4())
        self.user = get_user_model().objects.create_user(
            username="usuario_prueba",
            password="PruebaSegura123!"
        )
        self.client.force_authenticate(user=self.user)
        _, self.workspace = crear_workspace_prueba(usuario=self.user)
        self.client.credentials(
            HTTP_X_WORKSPACE_ID=str(self.workspace.pk)
        )
        self.problema = Problema.objects.create(
            workspace=self.workspace,
            nombre="Problema API IA",
            sentido_objetivo=Problema.SentidoObjetivo.MAXIMIZAR,
            estado=Problema.Estado.LISTO,
        )

        producto = Producto.objects.create(
            problema=self.problema,
            codigo="P1",
            nombre="Producto 1",
            utilidad_unitaria=Decimal("5.00"),
        )

        recurso = Recurso.objects.create(
            problema=self.problema,
            nombre="Recurso A",
            unidad_medida="kg",
            disponibilidad=Decimal("10.00"),
        )

        ConsumoRecurso.objects.create(
            producto=producto,
            recurso=recurso,
            cantidad_por_unidad=Decimal("2.0000"),
        )

        self.ejecucion = ejecutar_optimizacion(
            self.problema.id
        )

        self.url = (
            f"/api/analisis-ia/ejecuciones/"
            f"{self.ejecucion.id}/generar/"
        )

    @patch(
        "apps.inteligencia_artificial.services.analisis.generar_respuesta"
    )
    def test_generar_analisis_responde_201(self, mock_generar):
        mock_generar.return_value = {
            "contenido": "La solución óptima produce 5 unidades.",
            "modelo": "openai/gpt-oss-120b",
        }

        response = self.client.post(
            self.url,
            {
                "pregunta": "¿Cuánto producimos?",
                "consentimiento_confirmado": True,
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY=self.idempotency_key,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(AnalisisIA.objects.count(), 1)
        self.assertEqual(
            response.data["contenido"],
            "La solución óptima produce 5 unidades.",
        )
        self.assertEqual(
            AnalisisIA.objects.get().solicitado_por,
            self.user,
        )

    @patch(
        "apps.inteligencia_artificial.services.analisis.generar_respuesta"
    )
    def test_reintento_con_misma_clave_reutiliza_analisis(self, mock_generar):
        mock_generar.return_value = {
            "contenido": "Análisis único.",
            "modelo": "test-model",
        }
        payload = {
            "pregunta": "¿Cuánto producimos?",
            "consentimiento_confirmado": True,
        }

        first = self.client.post(
            self.url,
            payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY=self.idempotency_key,
        )
        self.ejecucion.snapshot_entrada = {}
        self.ejecucion.save(update_fields=["snapshot_entrada"])
        replay = self.client.post(
            self.url,
            payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY=self.idempotency_key,
        )

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(replay.status_code, status.HTTP_200_OK)
        self.assertEqual(first.data["id"], replay.data["id"])
        self.assertEqual(AnalisisIA.objects.count(), 1)
        self.assertEqual(SolicitudAnalisisIA.objects.count(), 1)
        mock_generar.assert_called_once()

    @patch("apps.inteligencia_artificial.services.analisis.generar_respuesta")
    def test_sin_sentido_historico_rechaza_nuevo_analisis(self, mock_generar):
        self.ejecucion.snapshot_entrada = {}
        self.ejecucion.save(update_fields=["snapshot_entrada"])

        respuesta = self.client.post(
            self.url,
            {"consentimiento_confirmado": True},
            format="json",
            HTTP_IDEMPOTENCY_KEY=self.idempotency_key,
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("sentido objetivo histórico", respuesta.data["error"])
        self.assertFalse(SolicitudAnalisisIA.objects.exists())
        mock_generar.assert_not_called()

    @patch(
        "apps.inteligencia_artificial.services.analisis.generar_respuesta"
    )
    def test_clave_no_se_puede_reutilizar_con_otros_datos(self, mock_generar):
        mock_generar.return_value = {
            "contenido": "Análisis único.",
            "modelo": "test-model",
        }
        response = self.client.post(
            self.url,
            {
                "pregunta": "Primera pregunta",
                "consentimiento_confirmado": True,
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY=self.idempotency_key,
        )
        conflict = self.client.post(
            self.url,
            {
                "pregunta": "Otra pregunta",
                "consentimiento_confirmado": True,
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY=self.idempotency_key,
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(conflict.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(AnalisisIA.objects.count(), 1)
        mock_generar.assert_called_once()

    def test_falta_clave_idempotente_rechaza_solicitud(self):
        response = self.client.post(
            self.url,
            {"consentimiento_confirmado": True},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(AnalisisIA.objects.count(), 0)
        self.assertEqual(SolicitudAnalisisIA.objects.count(), 0)

    def test_ejecucion_inexistente_responde_400(self):
        response = self.client.post(
            "/api/analisis-ia/ejecuciones/99999/generar/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertEqual(AnalisisIA.objects.count(), 0)

    def test_pregunta_excesivamente_larga_responde_400(self):
        response = self.client.post(
            self.url,
            {
                "pregunta": "A" * 5001,
                "consentimiento_confirmado": True,
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY=self.idempotency_key,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(AnalisisIA.objects.count(), 0)

    @patch(
        "apps.inteligencia_artificial.services.analisis.generar_respuesta"
    )
    def test_sin_consentimiento_no_contacta_al_proveedor(self, mock_generar):
        response = self.client.post(
            self.url,
            {"consentimiento_confirmado": False},
            format="json",
            HTTP_IDEMPOTENCY_KEY=self.idempotency_key,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        mock_generar.assert_not_called()
        self.assertEqual(AnalisisIA.objects.count(), 0)

    @patch(
        "apps.inteligencia_artificial.services.analisis.generar_respuesta"
    )
    def test_error_del_proveedor_responde_502(self, mock_generar):
        from apps.inteligencia_artificial.services.proveedor_ia import (
            ErrorProveedorIA,
        )

        mock_generar.side_effect = ErrorProveedorIA(
            "Error simulado de Groq."
        )

        response = self.client.post(
            self.url,
            {"consentimiento_confirmado": True},
            format="json",
            HTTP_IDEMPOTENCY_KEY=self.idempotency_key,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_502_BAD_GATEWAY,
        )

        self.assertEqual(AnalisisIA.objects.count(), 0)
        request = SolicitudAnalisisIA.objects.get()
        self.assertEqual(request.estado, SolicitudAnalisisIA.Estado.FAILED)
        retry = self.client.post(
            self.url,
            {"consentimiento_confirmado": True},
            format="json",
            HTTP_IDEMPOTENCY_KEY=self.idempotency_key,
        )
        self.assertEqual(retry.status_code, status.HTTP_409_CONFLICT)
        mock_generar.assert_called_once()
