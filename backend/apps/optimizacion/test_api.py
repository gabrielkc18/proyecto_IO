from django.contrib.auth import get_user_model

from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from apps.problemas.models import Problema
from apps.optimizacion.models import Ejecucion


class EjecucionAPITests(APITestCase):

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

        self.ejecucion = Ejecucion.objects.create(
            problema=self.problema
        )

        self.otra_ejecucion = Ejecucion.objects.create(
            problema=self.otro_problema
        )

        self.url = reverse("ejecucion-list")

    def test_listar_ejecuciones(self):
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(len(response.data), 2)

    def test_filtrar_ejecuciones_por_problema(self):
        response = self.client.get(
            self.url,
            {"problema": self.problema.id}
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(len(response.data), 1)

    def test_consultar_ejecucion(self):
        url = reverse(
            "ejecucion-detail",
            kwargs={"pk": self.ejecucion.pk}
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_no_permitir_crear_ejecucion(self):
        data = {
            "problema": self.problema.id,
            "estado_proceso": "TERMINADO",
            "utilidad_total": "15000.00"
        }

        response = self.client.post(
            self.url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_no_permitir_modificar_ejecucion(self):
        url = reverse(
            "ejecucion-detail",
            kwargs={"pk": self.ejecucion.pk}
        )

        response = self.client.patch(
            url,
            {"estado_proceso": "TERMINADO"},
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_no_permitir_eliminar_ejecucion(self):
        url = reverse(
            "ejecucion-detail",
            kwargs={"pk": self.ejecucion.pk}
        )

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

        self.assertTrue(
            Ejecucion.objects.filter(
                pk=self.ejecucion.pk
            ).exists()
        )
