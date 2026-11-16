from django.contrib.auth import get_user_model

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.problemas.models import Problema


class ProblemaAPITests(APITestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="usuario_prueba",
            password="PruebaSegura123!"
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse("problema-list")

        self.problema = Problema.objects.create(
            nombre="Producción industrial",
            descripcion="Optimización de producción",
            sentido_objetivo="MAXIMIZAR",
            estado="BORRADOR"
        )

    def test_listar_problemas(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_consultar_problema(self):
        url = reverse(
            "problema-detail",
            kwargs={"pk": self.problema.pk}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nombre"], "Producción industrial")

    def test_crear_problema(self):
        data = {
            "nombre": "Optimización de inventario",
            "descripcion": "Control de inventario",
            "sentido_objetivo": "MINIMIZAR",
            "estado": "BORRADOR"
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Problema.objects.filter(
                nombre="Optimización de inventario"
            ).exists()
        )

    def test_actualizar_problema(self):
        url = reverse(
            "problema-detail",
            kwargs={"pk": self.problema.pk}
        )

        data = {
            "nombre": "Producción actualizada"
        }

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.problema.refresh_from_db()

        self.assertEqual(
            self.problema.nombre,
            "Producción actualizada"
        )

    def test_eliminar_problema(self):
        url = reverse(
            "problema-detail",
            kwargs={"pk": self.problema.pk}
        )

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(
            Problema.objects.filter(pk=self.problema.pk).exists()
        )
