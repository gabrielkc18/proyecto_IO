
from decimal import Decimal
from unittest.mock import patch

from rest_framework.test import APITestCase
from rest_framework import status

from apps.problemas.models import Problema
from apps.productos.models import Producto
from apps.recursos.models import Recurso, ConsumoRecurso
from apps.optimizacion.services.ejecucion import ejecutar_optimizacion
from apps.inteligencia_artificial.models import AnalisisIA


class GenerarAnalisisAPITests(APITestCase):

    def setUp(self):
        self.problema = Problema.objects.create(
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
            {"pregunta": "¿Cuánto producimos?"},
            format="json",
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

    def test_ejecucion_inexistente_responde_400(self):
        response = self.client.post(
            "/api/analisis-ia/ejecuciones/99999/generar/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(AnalisisIA.objects.count(), 0)

    def test_pregunta_excesivamente_larga_responde_400(self):
        response = self.client.post(
            self.url,
            {"pregunta": "A" * 5001},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

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
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_502_BAD_GATEWAY,
        )

        self.assertEqual(AnalisisIA.objects.count(), 0)
