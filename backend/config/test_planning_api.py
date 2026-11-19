from unittest.mock import patch

from rest_framework.test import APITestCase

from apps.optimizacion.models import Ejecucion
from apps.problemas.models import Problema
from apps.productos.models import Producto
from apps.workspaces.test_utils import crear_workspace_prueba


class PlanningApiTests(APITestCase):
    def setUp(self):
        self.user, self.workspace = crear_workspace_prueba()
        self.client.force_authenticate(self.user)
        self.client.credentials(HTTP_X_WORKSPACE_ID=str(self.workspace.pk))
        self.problema = Problema.objects.create(workspace=self.workspace, nombre="Plan")

    def test_filtros_invalidos_responden_400(self):
        for ruta, filtro in (
            ("productos", "problema"),
            ("recursos", "problema"),
            ("consumos", "problema"),
            ("consumos", "producto"),
            ("consumos", "recurso"),
            ("ejecuciones", "problema"),
            ("resultados-productos", "ejecucion"),
            ("resultados-recursos", "problema"),
            ("analisis-ia", "ejecucion"),
        ):
            with self.subTest(ruta=ruta, filtro=filtro):
                respuesta = self.client.get(f"/api/{ruta}/", {filtro: "texto"})
                self.assertEqual(respuesta.status_code, 400)
                self.assertIn(filtro, respuesta.data)

    def test_id_de_workspace_y_de_ejecucion_invalidos(self):
        self.client.credentials(HTTP_X_WORKSPACE_ID=str(2**63))
        respuesta = self.client.get("/api/problemas/")
        self.assertEqual(respuesta.status_code, 400)
        self.client.credentials(HTTP_X_WORKSPACE_ID=str(self.workspace.pk))
        respuesta = self.client.get("/api/productos/", {"problema": "0"})
        self.assertEqual(respuesta.status_code, 400)
        respuesta = self.client.get("/api/productos/", {"problema": ""})
        self.assertEqual(respuesta.status_code, 400)
        respuesta = self.client.post("/api/problemas/texto/ejecutar/")
        self.assertEqual(respuesta.status_code, 400)

    def test_eliminar_problema_protegido_responde_409(self):
        ejecucion = Ejecucion.objects.create(problema=self.problema)
        respuesta = self.client.delete(f"/api/problemas/{self.problema.pk}/")
        self.assertEqual(respuesta.status_code, 409)
        self.assertIn("detail", respuesta.data)
        self.assertTrue(Ejecucion.objects.filter(pk=ejecucion.pk).exists())

    def test_patch_detecta_codigo_duplicado_sin_repetir_el_problema(self):
        Producto.objects.create(
            problema=self.problema, codigo="P1", nombre="Uno", utilidad_unitaria=1,
        )
        producto = Producto.objects.create(
            problema=self.problema, codigo="P2", nombre="Dos", utilidad_unitaria=1,
        )
        respuesta = self.client.patch(
            f"/api/productos/{producto.pk}/", {"codigo": "P1"}, format="json",
        )
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("codigo", respuesta.data)

    def test_conflicto_de_unicidad_al_guardar_responde_409(self):
        def guardar_con_duplicado(*args, **kwargs):
            return Problema.objects.create(workspace=self.workspace, nombre="Plan")

        with patch(
            "apps.problemas.serializers.ProblemaSerializer.save",
            side_effect=guardar_con_duplicado,
        ):
            respuesta = self.client.post(
                "/api/problemas/", {"nombre": "Otro"}, format="json",
            )

        self.assertEqual(respuesta.status_code, 409)
        self.assertIn("detail", respuesta.data)
        self.assertEqual(Problema.objects.count(), 1)

    def test_schema_publica_filtros_y_borrado_protegido(self):
        respuesta = self.client.get("/api/schema/")
        paths = respuesta.data["paths"]
        filtros = paths["/api/consumos/"]["get"]["parameters"]
        self.assertTrue(
            {"problema", "producto", "recurso"}.issubset(
                parametro["name"] for parametro in filtros
            )
        )
        self.assertIn("409", paths["/api/problemas/{id}/"]["delete"]["responses"])
