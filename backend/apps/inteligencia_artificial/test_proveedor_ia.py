from types import SimpleNamespace
from unittest.mock import patch

import httpx
from django.test import SimpleTestCase, override_settings
from groq import APIStatusError, APITimeoutError

from apps.inteligencia_artificial.services.proveedor_ia import (
    ErrorProveedorIA,
    generar_respuesta,
)


class ProveedorIATests(SimpleTestCase):
    @override_settings(GROQ_TIMEOUT_SECONDS=7)
    @patch("apps.inteligencia_artificial.services.proveedor_ia.Groq")
    @patch(
        "apps.inteligencia_artificial.services.proveedor_ia.config",
        side_effect=["test-key", "test-model"],
    )
    def test_configura_timeout_desactiva_reintentos_y_retorna_respuesta(
        self,
        mock_config,
        mock_groq,
    ):
        respuesta = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content="Análisis de prueba."),
                )
            ],
            model="test-model",
        )
        mock_groq.return_value.chat.completions.create.return_value = respuesta

        resultado = generar_respuesta(
            [{"role": "user", "content": "Analiza datos."}],
        )

        mock_groq.assert_called_once_with(
            api_key="test-key",
            timeout=7,
            max_retries=0,
        )
        self.assertEqual(mock_config.call_count, 2)
        self.assertEqual(
            resultado,
            {"contenido": "Análisis de prueba.", "modelo": "test-model"},
        )

    @patch("apps.inteligencia_artificial.services.proveedor_ia.Groq")
    @patch(
        "apps.inteligencia_artificial.services.proveedor_ia.config",
        side_effect=["test-key", "test-model"],
    )
    def test_timeout_del_proveedor_se_normaliza(
        self,
        mock_config,
        mock_groq,
    ):
        request = httpx.Request("POST", "https://api.groq.com")
        mock_groq.return_value.chat.completions.create.side_effect = (
            APITimeoutError(request=request)
        )

        with self.assertRaisesRegex(ErrorProveedorIA, "comunicarse"):
            generar_respuesta([{"role": "user", "content": "Analiza."}])
        self.assertEqual(mock_config.call_count, 2)

    @patch("apps.inteligencia_artificial.services.proveedor_ia.Groq")
    @patch(
        "apps.inteligencia_artificial.services.proveedor_ia.config",
        side_effect=["test-key", "test-model"],
    )
    def test_error_http_se_normaliza_sin_registrar_respuesta(
        self,
        mock_config,
        mock_groq,
    ):
        request = httpx.Request("POST", "https://api.groq.com")
        response = httpx.Response(
            429,
            request=request,
            json={"error": "contenido sensible"},
        )
        mock_groq.return_value.chat.completions.create.side_effect = (
            APIStatusError(
                "Rate limit",
                response=response,
                body={"error": "contenido sensible"},
            )
        )

        with self.assertLogs(
            "apps.inteligencia_artificial.services.proveedor_ia",
            level="WARNING",
        ) as logs:
            with self.assertRaisesRegex(ErrorProveedorIA, "comunicarse"):
                generar_respuesta(
                    [{"role": "user", "content": "Analiza."}],
                )

        self.assertNotIn("contenido sensible", "\n".join(logs.output))
        self.assertEqual(mock_config.call_count, 2)

    @patch("apps.inteligencia_artificial.services.proveedor_ia.Groq")
    @patch(
        "apps.inteligencia_artificial.services.proveedor_ia.config",
        side_effect=["test-key", "test-model"],
    )
    def test_respuesta_vacia_se_rechaza(
        self,
        mock_config,
        mock_groq,
    ):
        mock_groq.return_value.chat.completions.create.return_value = (
            SimpleNamespace(choices=[], model="test-model")
        )

        with self.assertRaisesRegex(ErrorProveedorIA, "inválida"):
            generar_respuesta([{"role": "user", "content": "Analiza."}])
        self.assertEqual(mock_config.call_count, 2)
