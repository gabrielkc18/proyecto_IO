
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from apps.problemas.models import Problema
from apps.workspaces.test_utils import (
    crear_workspace_prueba,
    crear_problema_prueba,
)


class ProblemaAPITests(APITestCase):

    def setUp(self):
        self.user, self.workspace = crear_workspace_prueba()

        self.client.force_authenticate(user=self.user)
        self.client.credentials(
            HTTP_X_WORKSPACE_ID=str(self.workspace.pk)
        )

        self.url = reverse("problema-list")

        self.problema = crear_problema_prueba(
            self.workspace,
            nombre="Producción industrial",
            descripcion="Optimización de producción",
            sentido_objetivo="MAXIMIZAR",
            estado="BORRADOR",
        )

    def test_listar_problemas(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_consultar_problema(self):
        url = reverse(
            "problema-detail",
            kwargs={"pk": self.problema.pk},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["nombre"],
            "Producción industrial",
        )

    def test_crear_problema(self):
        data = {
            "nombre": "Optimización de inventario",
            "descripcion": "Control de inventario",
            "sentido_objetivo": "MINIMIZAR",
            "estado": "BORRADOR",
        }

        response = self.client.post(
            self.url,
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            Problema.objects.filter(
                nombre="Optimización de inventario",
                workspace=self.workspace,
            ).exists()
        )

    def test_actualizar_problema(self):
        url = reverse(
            "problema-detail",
            kwargs={"pk": self.problema.pk},
        )

        response = self.client.patch(
            url,
            {"nombre": "Producción actualizada"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.problema.refresh_from_db()

        self.assertEqual(
            self.problema.nombre,
            "Producción actualizada",
        )

    def test_eliminar_problema(self):
        url = reverse(
            "problema-detail",
            kwargs={"pk": self.problema.pk},
        )

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Problema.objects.filter(pk=self.problema.pk).exists()
        )

    def test_no_permite_listar_sin_workspace(self):
        self.client.credentials()

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_no_permite_acceder_a_workspace_de_otro_usuario(self):
        _, otro_workspace = crear_workspace_prueba(
            nombre="Workspace privado de otro usuario",
        )

        self.client.credentials(
            HTTP_X_WORKSPACE_ID=str(otro_workspace.pk)
        )

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_no_permite_consultar_problema_de_otro_workspace(self):
        _, otro_workspace = crear_workspace_prueba(
            nombre="Workspace externo",
        )

        problema_externo = crear_problema_prueba(
            otro_workspace,
            nombre="Problema privado",
        )

        url = reverse(
            "problema-detail",
            kwargs={"pk": problema_externo.pk},
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_no_permite_crear_sin_workspace(self):
        self.client.credentials()

        response = self.client.post(
            self.url,
            {"nombre": "Problema sin contexto"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_no_permite_enviar_workspace_en_el_cuerpo(self):
        _, otro_workspace = crear_workspace_prueba(
            nombre="Workspace que no debe poder asignarse",
        )

        response = self.client.post(
            self.url,
            {
                "nombre": "Intento de asignación externa",
                "workspace": otro_workspace.pk,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        problema = Problema.objects.get(
            nombre="Intento de asignación externa",
            workspace=self.workspace,
        )

        self.assertNotEqual(
            problema.workspace_id,
            otro_workspace.pk,
        )
