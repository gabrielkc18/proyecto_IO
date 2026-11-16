from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase


class JWTAuthenticationAPITests(APITestCase):

    def setUp(self):
        self.password = "PruebaSegura123!"

        self.user = get_user_model().objects.create_user(
            username="usuario_jwt",
            password=self.password
        )

        self.token_url = reverse("token_obtain_pair")
        self.refresh_url = reverse("token_refresh")
        self.problemas_url = reverse("problema-list")

    def obtener_tokens(self):
        return self.client.post(
            self.token_url,
            {
                "username": self.user.username,
                "password": self.password
            },
            format="json"
        )

    def test_obtener_tokens_con_credenciales_validas(self):
        response = self.obtener_tokens()

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_rechazar_credenciales_incorrectas(self):
        response = self.client.post(
            self.token_url,
            {
                "username": self.user.username,
                "password": "ClaveIncorrecta123!"
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_renovar_access_token(self):
        tokens = self.obtener_tokens()

        refresh = tokens.data["refresh"]

        response = self.client.post(
            self.refresh_url,
            {"refresh": refresh},
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertIn("access", response.data)

    def test_rechazar_acceso_sin_autenticacion(self):
        response = self.client.get(self.problemas_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_permitir_acceso_con_access_token_valido(self):
        tokens = self.obtener_tokens()

        access = tokens.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access}"
        )

        response = self.client.get(self.problemas_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
