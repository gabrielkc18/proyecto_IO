from unittest.mock import patch

from django.db import DatabaseError
from django.test import TestCase
from rest_framework.test import APITestCase


class HealthCheckTests(TestCase):
    def test_health_check_confirma_conectividad_de_base_de_datos(self):
        response = self.client.get("/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @patch(
        "config.views.connection.cursor",
        side_effect=DatabaseError("detalle interno"),
    )
    def test_health_check_no_expone_detalles_de_base_de_datos(
        self,
        mock_cursor,
    ):
        with self.assertLogs("config.views", level="ERROR") as logs:
            response = self.client.get("/health/")

        mock_cursor.assert_called_once()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unavailable"})
        self.assertNotIn("detalle interno", response.content.decode())
        self.assertNotIn("detalle interno", "\n".join(logs.output))


class OpenAPISchemaTests(APITestCase):
    def test_schema_documents_account_workspace_and_ai_contracts(self):
        response = self.client.get("/api/schema/")

        self.assertEqual(response.status_code, 200)
        schema = response.data
        self.assertEqual(schema["openapi"], "3.0.3")

        paths = schema["paths"]
        self.assertIn("/api/auth/registro/", paths)
        self.assertIn("/health/", paths)
        self.assertIn("/api/workspaces/{workspace_id}/miembros/", paths)
        self.assertIn(
            "/api/analisis-ia/ejecuciones/{ejecucion_id}/generar/",
            paths,
        )
        self.assertIn("/api/problemas/{id}/ejecutar/", paths)

        registration = paths["/api/auth/registro/"]["post"]
        self.assertIn("application/json", registration["requestBody"]["content"])
        self.assertIn("201", registration["responses"])
        self.assertEqual(registration["security"], [{}])

        problem_list = paths["/api/problemas/"]["get"]
        parameter_names = {
            parameter["name"]
            for parameter in problem_list["parameters"]
        }
        self.assertTrue(
            {"X-Workspace-ID", "page", "page_size"}.issubset(parameter_names)
        )
        self.assertIn(
            {"jwtAuth": []},
            problem_list["security"],
        )

        member_create = paths[
            "/api/workspaces/{workspace_id}/miembros/"
        ]["post"]
        self.assertIn("application/json", member_create["requestBody"]["content"])
        self.assertIn("201", member_create["responses"])

        ai_request = paths[
            "/api/analisis-ia/ejecuciones/{ejecucion_id}/generar/"
        ]["post"]
        idempotency_parameter = next(
            parameter
            for parameter in ai_request["parameters"]
            if parameter["name"] == "Idempotency-Key"
        )
        self.assertTrue(idempotency_parameter["required"])
        self.assertEqual(
            idempotency_parameter["schema"]["format"],
            "uuid",
        )
        self.assertIn("201", ai_request["responses"])
        self.assertIn("503", paths["/health/"]["get"]["responses"])

        self.assertIn(
            {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
            schema["components"]["securitySchemes"].values(),
        )

    def test_swagger_ui_is_available(self):
        response = self.client.get("/api/docs/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response["Content-Type"])
