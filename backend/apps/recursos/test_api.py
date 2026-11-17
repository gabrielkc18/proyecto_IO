from django.contrib.auth import get_user_model

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.problemas.models import Problema
from apps.recursos.models import Recurso
from apps.workspaces.test_utils import crear_workspace_prueba, crear_problema_prueba


class RecursoAPITests(APITestCase):

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

        self.problema = crear_problema_prueba(
            self.workspace, nombre="Producción industrial"
        )

        self.otro_problema = crear_problema_prueba(
            self.workspace, nombre="Producción secundaria"
        )

        self.recurso = Recurso.objects.create(
            problema=self.problema,
            nombre="Materia prima A",
            unidad_medida="kg",
            disponibilidad=3000
        )

        self.otro_recurso = Recurso.objects.create(
            problema=self.otro_problema,
            nombre="Materia prima A",
            unidad_medida="kg",
            disponibilidad=2500
        )

        self.url = reverse("recurso-list")

    def test_listar_recursos(self):
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(len(response.data["results"]), 2)

    def test_filtrar_recursos_por_problema(self):
        response = self.client.get(
            self.url,
            {"problema": self.problema.id}
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["nombre"],
            "Materia prima A"
        )

    def test_consultar_recurso(self):
        url = reverse(
            "recurso-detail",
            kwargs={"pk": self.recurso.pk}
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.data["nombre"],
            "Materia prima A"
        )

    def test_crear_recurso(self):
        data = {
            "problema": self.problema.id,
            "nombre": "Horas máquina",
            "unidad_medida": "h",
            "disponibilidad": "1600.00",
            "activo": True
        }

        response = self.client.post(
            self.url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertTrue(
            Recurso.objects.filter(
                problema=self.problema,
                nombre="Horas máquina"
            ).exists()
        )

    def test_actualizar_recurso(self):
        url = reverse(
            "recurso-detail",
            kwargs={"pk": self.recurso.pk}
        )

        response = self.client.patch(
            url,
            {"disponibilidad": "3500.00"},
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.recurso.refresh_from_db()

        self.assertEqual(
            self.recurso.disponibilidad,
            3500
        )

    def test_eliminar_recurso(self):
        url = reverse(
            "recurso-detail",
            kwargs={"pk": self.recurso.pk}
        )

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT
        )

        self.assertFalse(
            Recurso.objects.filter(
                pk=self.recurso.pk
            ).exists()
        )


    def test_rechazar_peticion_sin_workspace(self):
        self.client.credentials()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_no_permitir_workspace_de_otro_usuario(self):
        otro_usuario, otro_workspace = crear_workspace_prueba()
        self.client.credentials(
            HTTP_X_WORKSPACE_ID=str(otro_workspace.pk)
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_no_permitir_consultar_recurso_de_otro_workspace(self):
        otro_usuario, otro_workspace = crear_workspace_prueba()
        problema_externo = crear_problema_prueba(
            otro_workspace, nombre="Problema externo"
        )
        recurso_externo = Recurso.objects.create(
            problema=problema_externo,
            nombre="Recurso externo",
            unidad_medida="kg",
            disponibilidad=100,
        )

        self.client.credentials(
            HTTP_X_WORKSPACE_ID=str(self.workspace.pk)
        )
        url = reverse(
            "recurso-detail",
            kwargs={"pk": recurso_externo.pk},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_no_permitir_asignar_problema_de_otro_workspace(self):
        otro_usuario, otro_workspace = crear_workspace_prueba()
        problema_externo = crear_problema_prueba(
            otro_workspace, nombre="Problema externo"
        )
        response = self.client.post(
            self.url,
            {
                "problema": problema_externo.pk,
                "nombre": "Recurso no autorizado",
                "unidad_medida": "kg",
                "disponibilidad": "100",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
