from django.contrib.auth import get_user_model

from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from apps.problemas.models import Problema
from apps.optimizacion.models import Ejecucion
from apps.inteligencia_artificial.models import AnalisisIA
from apps.workspaces.test_utils import crear_workspace_prueba
from apps.workspaces.test_utils import crear_problema_prueba


class AnalisisIAAPITests(APITestCase):

    def setUp(self):
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
            nombre="Producción industrial"
        )

        self.otro_problema = Problema.objects.create(
            workspace=self.workspace,
            nombre="Producción secundaria"
        )

        self.ejecucion = Ejecucion.objects.create(
            problema=self.problema
        )

        self.otra_ejecucion = Ejecucion.objects.create(
            problema=self.otro_problema
        )

        self.analisis = AnalisisIA.objects.create(
            ejecucion=self.ejecucion,
            tipo_analisis="GENERAL",
            pregunta="¿Qué indican los resultados?",
            contenido="La producción presenta una utilidad favorable.",
            modelo_ia="modelo-prueba",
            contexto_enviado={
                "utilidad_total": 15000
            }
        )

        self.url = reverse("analisis-ia-list")

    def test_listar_analisis(self):
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(len(response.data), 1)

    def test_filtrar_analisis_por_ejecucion(self):
        response = self.client.get(
            self.url,
            {"ejecucion": self.ejecucion.id}
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(len(response.data), 1)

    def test_filtrar_analisis_por_problema(self):
        response = self.client.get(
            self.url,
            {"problema": self.problema.id}
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(len(response.data), 1)

    def test_consultar_analisis(self):
        url = reverse(
            "analisis-ia-detail",
            kwargs={"pk": self.analisis.pk}
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data["contenido"],
            "La producción presenta una utilidad favorable."
        )

    def test_no_permitir_crear_analisis(self):
        response = self.client.post(
            self.url,
            {},
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_no_permitir_modificar_analisis(self):
        url = reverse(
            "analisis-ia-detail",
            kwargs={"pk": self.analisis.pk}
        )

        response = self.client.patch(
            url,
            {"contenido": "Contenido modificado"},
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_no_permitir_eliminar_analisis(self):
        url = reverse(
            "analisis-ia-detail",
            kwargs={"pk": self.analisis.pk}
        )

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

        self.assertTrue(
            AnalisisIA.objects.filter(
                pk=self.analisis.pk
            ).exists()
        )

    def test_no_listar_analisis_de_otro_workspace(self):
        _, otro_workspace = crear_workspace_prueba()
        problema_externo = crear_problema_prueba(
            otro_workspace,
            nombre="Problema externo",
        )
        ejecucion_externa = Ejecucion.objects.create(
            problema=problema_externo,
        )
        analisis_externo = AnalisisIA.objects.create(
            ejecucion=ejecucion_externa,
            tipo_analisis="GENERAL",
            pregunta="Pregunta externa",
            contenido="Análisis externo",
            modelo_ia="modelo-prueba",
            contexto_enviado={},
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data]
        self.assertNotIn(analisis_externo.pk, ids)
        self.assertEqual(len(response.data), 1)

    def test_no_consultar_analisis_de_otro_workspace(self):
        _, otro_workspace = crear_workspace_prueba()
        problema_externo = crear_problema_prueba(
            otro_workspace,
            nombre="Problema externo",
        )
        ejecucion_externa = Ejecucion.objects.create(
            problema=problema_externo,
        )
        analisis_externo = AnalisisIA.objects.create(
            ejecucion=ejecucion_externa,
            tipo_analisis="GENERAL",
            pregunta="Pregunta externa",
            contenido="Análisis externo",
            modelo_ia="modelo-prueba",
            contexto_enviado={},
        )

        url = reverse(
            "analisis-ia-detail",
            kwargs={"pk": analisis_externo.pk},
        )
        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
