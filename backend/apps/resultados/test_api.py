from django.contrib.auth import get_user_model

from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from apps.problemas.models import Problema
from apps.productos.models import Producto
from apps.recursos.models import Recurso
from apps.optimizacion.models import Ejecucion
from apps.resultados.models import (
    ResultadoProducto,
    ResultadoRecurso
)
from apps.workspaces.test_utils import crear_workspace_prueba
from apps.workspaces.test_utils import crear_problema_prueba


class ResultadosAPITests(APITestCase):

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

        self.producto = Producto.objects.create(
            problema=self.problema,
            codigo="P1",
            nombre="Producto 1",
            utilidad_unitaria=80
        )

        self.recurso = Recurso.objects.create(
            problema=self.problema,
            nombre="Materia prima A",
            unidad_medida="kg",
            disponibilidad=3000
        )

        self.resultado_producto = ResultadoProducto.objects.create(
            ejecucion=self.ejecucion,
            producto=self.producto,
            nombre_producto="Producto 1",
            utilidad_unitaria=80,
            cantidad=100,
            utilidad_aportada=8000
        )

        self.resultado_recurso = ResultadoRecurso.objects.create(
            ejecucion=self.ejecucion,
            recurso=self.recurso,
            nombre_recurso="Materia prima A",
            unidad_medida="kg",
            disponibilidad=3000,
            consumo_total=2500,
            holgura=500,
            estado_uso="CON_HOLGURA"
        )

        self.productos_url = reverse("resultado-producto-list")
        self.recursos_url = reverse("resultado-recurso-list")

    # RESULTADOS DE PRODUCTOS

    def test_listar_resultados_productos(self):
        response = self.client.get(self.productos_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(len(response.data["results"]), 1)

    def test_filtrar_resultados_productos_por_ejecucion(self):
        response = self.client.get(
            self.productos_url,
            {"ejecucion": self.ejecucion.id}
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(len(response.data["results"]), 1)

    def test_filtrar_resultados_productos_por_problema(self):
        response = self.client.get(
            self.productos_url,
            {"problema": self.problema.id}
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(len(response.data["results"]), 1)

    def test_consultar_resultado_producto(self):
        url = reverse(
            "resultado-producto-detail",
            kwargs={"pk": self.resultado_producto.pk}
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_no_permitir_crear_resultado_producto(self):
        response = self.client.post(
            self.productos_url,
            {},
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

    # RESULTADOS DE RECURSOS

    def test_listar_resultados_recursos(self):
        response = self.client.get(self.recursos_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(len(response.data["results"]), 1)

    def test_filtrar_resultados_recursos_por_ejecucion(self):
        response = self.client.get(
            self.recursos_url,
            {"ejecucion": self.ejecucion.id}
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(len(response.data["results"]), 1)

    def test_filtrar_resultados_recursos_por_problema(self):
        response = self.client.get(
            self.recursos_url,
            {"problema": self.problema.id}
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(len(response.data["results"]), 1)

    def test_consultar_resultado_recurso(self):
        url = reverse(
            "resultado-recurso-detail",
            kwargs={"pk": self.resultado_recurso.pk}
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_no_permitir_crear_resultado_recurso(self):
        response = self.client.post(
            self.recursos_url,
            {},
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_no_listar_resultados_producto_de_otro_workspace(self):
        _, otro_workspace = crear_workspace_prueba()
        problema_externo = crear_problema_prueba(
            otro_workspace,
            nombre="Problema externo",
        )
        producto_externo = Producto.objects.create(
            problema=problema_externo,
            codigo="EXT-P1",
            nombre="Producto externo",
            utilidad_unitaria=80,
        )
        ejecucion_externa = Ejecucion.objects.create(
            problema=problema_externo,
        )
        resultado_externo = ResultadoProducto.objects.create(
            ejecucion=ejecucion_externa,
            producto=producto_externo,
            nombre_producto="Producto externo",
            utilidad_unitaria=80,
            cantidad=10,
            utilidad_aportada=800,
        )

        response = self.client.get(self.productos_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["results"]]
        self.assertNotIn(resultado_externo.pk, ids)
        self.assertEqual(len(response.data["results"]), 1)

    def test_no_consultar_resultado_producto_de_otro_workspace(self):
        _, otro_workspace = crear_workspace_prueba()
        problema_externo = crear_problema_prueba(
            otro_workspace,
            nombre="Problema externo",
        )
        producto_externo = Producto.objects.create(
            problema=problema_externo,
            codigo="EXT-P2",
            nombre="Producto externo",
            utilidad_unitaria=80,
        )
        ejecucion_externa = Ejecucion.objects.create(
            problema=problema_externo,
        )
        resultado_externo = ResultadoProducto.objects.create(
            ejecucion=ejecucion_externa,
            producto=producto_externo,
            nombre_producto="Producto externo",
            utilidad_unitaria=80,
            cantidad=10,
            utilidad_aportada=800,
        )

        url = reverse(
            "resultado-producto-detail",
            kwargs={"pk": resultado_externo.pk},
        )
        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_no_listar_resultados_recurso_de_otro_workspace(self):
        _, otro_workspace = crear_workspace_prueba()
        problema_externo = crear_problema_prueba(
            otro_workspace,
            nombre="Problema externo",
        )
        recurso_externo = Recurso.objects.create(
            problema=problema_externo,
            nombre="Recurso externo",
            unidad_medida="kg",
            disponibilidad=3000,
        )
        ejecucion_externa = Ejecucion.objects.create(
            problema=problema_externo,
        )
        resultado_externo = ResultadoRecurso.objects.create(
            ejecucion=ejecucion_externa,
            recurso=recurso_externo,
            nombre_recurso="Recurso externo",
            unidad_medida="kg",
            disponibilidad=3000,
            consumo_total=2500,
            holgura=500,
            estado_uso="CON_HOLGURA",
        )

        response = self.client.get(self.recursos_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["results"]]
        self.assertNotIn(resultado_externo.pk, ids)
        self.assertEqual(len(response.data["results"]), 1)

    def test_no_consultar_resultado_recurso_de_otro_workspace(self):
        _, otro_workspace = crear_workspace_prueba()
        problema_externo = crear_problema_prueba(
            otro_workspace,
            nombre="Problema externo",
        )
        recurso_externo = Recurso.objects.create(
            problema=problema_externo,
            nombre="Recurso externo",
            unidad_medida="kg",
            disponibilidad=3000,
        )
        ejecucion_externa = Ejecucion.objects.create(
            problema=problema_externo,
        )
        resultado_externo = ResultadoRecurso.objects.create(
            ejecucion=ejecucion_externa,
            recurso=recurso_externo,
            nombre_recurso="Recurso externo",
            unidad_medida="kg",
            disponibilidad=3000,
            consumo_total=2500,
            holgura=500,
            estado_uso="CON_HOLGURA",
        )

        url = reverse(
            "resultado-recurso-detail",
            kwargs={"pk": resultado_externo.pk},
        )
        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
