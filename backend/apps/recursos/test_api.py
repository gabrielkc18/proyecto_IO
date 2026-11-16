from django.contrib.auth import get_user_model

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.problemas.models import Problema
from apps.recursos.models import Recurso


class RecursoAPITests(APITestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="usuario_prueba",
            password="PruebaSegura123!"
        )
        self.client.force_authenticate(user=self.user)
        self.problema = Problema.objects.create(
            nombre="Producción industrial"
        )

        self.otro_problema = Problema.objects.create(
            nombre="Producción secundaria"
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
        self.assertEqual(len(response.data), 2)

    def test_filtrar_recursos_por_problema(self):
        response = self.client.get(
            self.url,
            {"problema": self.problema.id}
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["nombre"],
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
