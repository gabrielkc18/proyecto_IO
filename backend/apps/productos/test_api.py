
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.problemas.models import Problema
from apps.productos.models import Producto


class ProductoAPITests(APITestCase):

    def setUp(self):
        self.problema = Problema.objects.create(
            nombre="Producción industrial"
        )

        self.otro_problema = Problema.objects.create(
            nombre="Producción secundaria"
        )

        self.producto = Producto.objects.create(
            problema=self.problema,
            codigo="P1",
            nombre="Producto 1",
            utilidad_unitaria=80
        )

        self.otro_producto = Producto.objects.create(
            problema=self.otro_problema,
            codigo="P1",
            nombre="Producto 2",
            utilidad_unitaria=100
        )

        self.url = reverse("producto-list")

    def test_listar_productos(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_filtrar_productos_por_problema(self):
        response = self.client.get(
            self.url,
            {"problema": self.problema.id}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["codigo"],
            "P1"
        )

    def test_consultar_producto(self):
        url = reverse(
            "producto-detail",
            kwargs={"pk": self.producto.pk}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nombre"], "Producto 1")

    def test_crear_producto(self):
        data = {
            "problema": self.problema.id,
            "codigo": "P2",
            "nombre": "Producto nuevo",
            "utilidad_unitaria": "120.00",
            "activo": True
        }

        response = self.client.post(
            self.url,
            data,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(
            Producto.objects.filter(
                problema=self.problema,
                codigo="P2"
            ).exists()
        )

    def test_actualizar_producto(self):
        url = reverse(
            "producto-detail",
            kwargs={"pk": self.producto.pk}
        )

        response = self.client.patch(
            url,
            {"nombre": "Producto actualizado"},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.producto.refresh_from_db()

        self.assertEqual(
            self.producto.nombre,
            "Producto actualizado"
        )

    def test_eliminar_producto(self):
        url = reverse(
            "producto-detail",
            kwargs={"pk": self.producto.pk}
        )

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT
        )

        self.assertFalse(
            Producto.objects.filter(
                pk=self.producto.pk
            ).exists()
        )
