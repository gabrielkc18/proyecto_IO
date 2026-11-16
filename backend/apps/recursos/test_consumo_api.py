from django.contrib.auth import get_user_model

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.problemas.models import Problema
from apps.productos.models import Producto
from apps.recursos.models import Recurso, ConsumoRecurso
from apps.workspaces.test_utils import crear_workspace_prueba, crear_problema_prueba


class ConsumoRecursoAPITests(APITestCase):

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

        self.recurso = Recurso.objects.create(
            problema=self.problema,
            nombre="Materia prima A",
            unidad_medida="kg",
            disponibilidad=3000
        )

        self.otro_recurso = Recurso.objects.create(
            problema=self.otro_problema,
            nombre="Materia prima B",
            unidad_medida="kg",
            disponibilidad=2500
        )

        self.consumo = ConsumoRecurso.objects.create(
            producto=self.producto,
            recurso=self.recurso,
            cantidad_por_unidad=4
        )

        self.url = reverse("consumo-list")

    def test_listar_consumos(self):
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(len(response.data), 1)

    def test_filtrar_consumos_por_problema(self):
        response = self.client.get(
            self.url,
            {"problema": self.problema.id}
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(len(response.data), 1)

    def test_filtrar_consumos_por_producto(self):
        response = self.client.get(
            self.url,
            {"producto": self.producto.id}
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(len(response.data), 1)

    def test_crear_consumo(self):
        data = {
            "producto": self.producto.id,
            "recurso": self.otro_recurso.id,
            "cantidad_por_unidad": "2.0000"
        }

        response = self.client.post(
            self.url,
            data,
            format="json"
        )

        # El producto y el recurso pertenecen
        # a problemas diferentes.
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_rechazar_cantidad_negativa(self):
        data = {
            "producto": self.producto.id,
            "recurso": self.recurso.id,
            "cantidad_por_unidad": "-2.0000"
        }

        response = self.client.post(
            self.url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_consultar_consumo(self):
        url = reverse(
            "consumo-detail",
            kwargs={"pk": self.consumo.pk}
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_actualizar_consumo(self):
        url = reverse(
            "consumo-detail",
            kwargs={"pk": self.consumo.pk}
        )

        response = self.client.patch(
            url,
            {"cantidad_por_unidad": "5.0000"},
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.consumo.refresh_from_db()

        self.assertEqual(
            self.consumo.cantidad_por_unidad,
            5
        )

    def test_eliminar_consumo(self):
        url = reverse(
            "consumo-detail",
            kwargs={"pk": self.consumo.pk}
        )

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT
        )

        self.assertFalse(
            ConsumoRecurso.objects.filter(
                pk=self.consumo.pk
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

    def test_no_permitir_consultar_consumo_de_otro_workspace(self):
        otro_usuario, otro_workspace = crear_workspace_prueba()
        problema_externo = crear_problema_prueba(
            otro_workspace, nombre="Problema externo"
        )
        producto_externo = Producto.objects.create(
            problema=problema_externo,
            codigo="EXT1",
            nombre="Producto externo",
            utilidad_unitaria=10,
        )
        recurso_externo = Recurso.objects.create(
            problema=problema_externo,
            nombre="Recurso externo",
            unidad_medida="kg",
            disponibilidad=100,
        )
        consumo_externo = ConsumoRecurso.objects.create(
            producto=producto_externo,
            recurso=recurso_externo,
            cantidad_por_unidad=2,
        )

        self.client.credentials(
            HTTP_X_WORKSPACE_ID=str(self.workspace.pk)
        )
        url = reverse(
            "consumo-detail",
            kwargs={"pk": consumo_externo.pk},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
