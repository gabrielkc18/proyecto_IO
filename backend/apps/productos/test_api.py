from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from apps.productos.models import Producto
from apps.workspaces.test_utils import (
    crear_workspace_prueba,
    crear_problema_prueba,
)


class ProductoAPITests(APITestCase):

    def setUp(self):
        self.user, self.workspace = crear_workspace_prueba()

        self.client.force_authenticate(user=self.user)
        self.client.credentials(
            HTTP_X_WORKSPACE_ID=str(self.workspace.pk)
        )

        self.problema = crear_problema_prueba(
            self.workspace,
            nombre="Producción industrial",
        )

        self.otro_problema = crear_problema_prueba(
            self.workspace,
            nombre="Producción secundaria",
        )

        self.producto = Producto.objects.create(
            problema=self.problema,
            codigo="P1",
            nombre="Producto 1",
            utilidad_unitaria=80,
        )

        self.otro_producto = Producto.objects.create(
            problema=self.otro_problema,
            codigo="P1",
            nombre="Producto 2",
            utilidad_unitaria=100,
        )

        self.url = reverse("producto-list")

    def test_listar_productos(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_paginacion_devuelve_metadatos_y_orden_estable(self):
        response = self.client.get(self.url, {"page_size": 1})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertIsNotNone(response.data["next"])
        self.assertEqual(response.data["results"][0]["id"], self.producto.pk)

    def test_filtrar_productos_por_problema(self):
        response = self.client.get(
            self.url,
            {"problema": self.problema.id},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["codigo"], "P1")

    def test_consultar_producto(self):
        url = reverse(
            "producto-detail",
            kwargs={"pk": self.producto.pk},
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
            "activo": True,
        }

        response = self.client.post(
            self.url,
            data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(
            Producto.objects.filter(
                problema=self.problema,
                codigo="P2",
            ).exists()
        )

    def test_actualizar_producto(self):
        url = reverse(
            "producto-detail",
            kwargs={"pk": self.producto.pk},
        )

        response = self.client.patch(
            url,
            {"nombre": "Producto actualizado"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.producto.refresh_from_db()

        self.assertEqual(
            self.producto.nombre,
            "Producto actualizado",
        )

    def test_no_permite_reasignar_producto_a_otro_problema_del_workspace(self):
        destino = crear_problema_prueba(self.workspace, nombre="Otro problema")
        url = reverse("producto-detail", kwargs={"pk": self.producto.pk})

        respuesta = self.client.patch(url, {"problema": destino.pk}, format="json")

        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("problema", respuesta.data)
        self.producto.refresh_from_db()
        self.assertNotEqual(self.producto.problema_id, destino.pk)

    def test_eliminar_producto(self):
        url = reverse(
            "producto-detail",
            kwargs={"pk": self.producto.pk},
        )

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Producto.objects.filter(pk=self.producto.pk).exists()
        )

    def test_no_permite_acceder_a_workspace_de_otro_usuario(self):
        _, otro_workspace = crear_workspace_prueba(
            nombre="Workspace ajeno",
        )

        self.client.credentials(
            HTTP_X_WORKSPACE_ID=str(otro_workspace.pk)
        )

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_no_permite_consultar_producto_de_otro_workspace(self):
        _, otro_workspace = crear_workspace_prueba(
            nombre="Workspace externo",
        )

        problema_externo = crear_problema_prueba(
            otro_workspace,
            nombre="Problema externo",
        )

        producto_externo = Producto.objects.create(
            problema=problema_externo,
            codigo="PX",
            nombre="Producto externo",
            utilidad_unitaria=50,
        )

        url = reverse(
            "producto-detail",
            kwargs={"pk": producto_externo.pk},
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_no_permite_asignar_producto_a_problema_externo(self):
        _, otro_workspace = crear_workspace_prueba(
            nombre="Workspace externo",
        )

        problema_externo = crear_problema_prueba(
            otro_workspace,
            nombre="Problema externo",
        )

        response = self.client.post(
            self.url,
            {
                "problema": problema_externo.pk,
                "codigo": "PX",
                "nombre": "Intento externo",
                "utilidad_unitaria": "50.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertFalse(
            Producto.objects.filter(codigo="PX").exists()
        )

    def test_no_permite_listar_sin_workspace(self):
        self.client.credentials()

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
