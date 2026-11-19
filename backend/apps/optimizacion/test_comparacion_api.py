from decimal import Decimal

from rest_framework.test import APITestCase

from apps.optimizacion.models import Ejecucion
from apps.problemas.models import Problema
from apps.productos.models import Producto
from apps.recursos.models import Recurso
from apps.resultados.models import ResultadoProducto, ResultadoRecurso
from apps.workspaces.models import WorkspaceMembership
from apps.workspaces.test_utils import crear_workspace_prueba


class ComparacionEjecucionesApiTests(APITestCase):
    def setUp(self):
        self.usuario, self.workspace = crear_workspace_prueba()
        self.client.force_authenticate(self.usuario)
        self.client.credentials(HTTP_X_WORKSPACE_ID=str(self.workspace.pk))
        self.problema = Problema.objects.create(workspace=self.workspace, nombre="Plan")
        self.base = self.crear_ejecucion(self.problema, "10.50")
        self.contra = self.crear_ejecucion(self.problema, "12.25")
        self.url = f"/api/ejecuciones/{self.base.pk}/comparar/"

    @staticmethod
    def crear_ejecucion(problema, utilidad):
        return Ejecucion.objects.create(
            problema=problema,
            estado_proceso=Ejecucion.EstadoProceso.TERMINADO,
            estado_solver=Ejecucion.EstadoSolver.OPTIMAL,
            utilidad_total=Decimal(utilidad),
            snapshot_entrada={"sentido_objetivo": "MAXIMIZAR"},
        )

    def test_compara_resultados_historicos_con_deltas_exactos(self):
        producto = Producto.objects.create(
            problema=self.problema, codigo="P1", nombre="Nombre actual", utilidad_unitaria=5,
        )
        producto_nuevo = Producto.objects.create(
            problema=self.problema, codigo="P2", nombre="Nuevo", utilidad_unitaria=1,
        )
        recurso = Recurso.objects.create(
            problema=self.problema, nombre="Recurso actual", disponibilidad=20, unidad_medida="kg",
        )
        for ejecucion, nombre, cantidad, consumo, holgura in (
            (self.base, "Nombre histórico base", 3, "10.10", "9.90"),
            (self.contra, "Nombre histórico nuevo", 2, "12.25", "7.75"),
        ):
            ResultadoProducto.objects.create(
                ejecucion=ejecucion, producto=producto, nombre_producto=nombre,
                utilidad_unitaria=5, cantidad=cantidad, utilidad_aportada=5 * cantidad,
            )
            ResultadoRecurso.objects.create(
                ejecucion=ejecucion, recurso=recurso, nombre_recurso="Recurso histórico",
                unidad_medida="kg", disponibilidad=20, consumo_total=consumo,
                holgura=holgura, estado_uso=ResultadoRecurso.EstadoUso.CON_HOLGURA,
            )
        ResultadoProducto.objects.create(
            ejecucion=self.contra, producto=producto_nuevo, nombre_producto="Nuevo",
            utilidad_unitaria=1, cantidad=1, utilidad_aportada=1,
        )

        respuesta = self.client.get(self.url, {"contra": self.contra.pk})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data["delta_utilidad_total"], "1.75")
        fila, agregado = respuesta.data["productos"]
        self.assertEqual(fila["base"]["nombre_producto"], "Nombre histórico base")
        self.assertEqual(fila["contra"]["nombre_producto"], "Nombre histórico nuevo")
        self.assertEqual(fila["delta"], {"cantidad": -1, "utilidad_aportada": "-5.00"})
        self.assertIsNone(agregado["base"])
        self.assertIsNone(agregado["delta"])
        self.assertEqual(
            respuesta.data["recursos"][0]["delta"],
            {"consumo_total": "2.15", "holgura": "-2.15"},
        )

        ResultadoRecurso.objects.filter(ejecucion=self.contra).update(unidad_medida="g")
        respuesta = self.client.get(self.url, {"contra": self.contra.pk})
        self.assertEqual(respuesta.data["recursos"][0]["contra"]["unidad_medida"], "g")
        self.assertIsNone(respuesta.data["recursos"][0]["delta"])

    def test_valida_ids_problema_y_estado(self):
        for contra in ("texto", self.base.pk):
            with self.subTest(contra=contra):
                self.assertEqual(self.client.get(self.url, {"contra": contra}).status_code, 400)
        self.assertEqual(self.client.get(self.url).status_code, 400)
        problema = Problema.objects.create(workspace=self.workspace, nombre="Otro")
        otra = self.crear_ejecucion(problema, "0.00")
        self.assertEqual(self.client.get(self.url, {"contra": otra.pk}).status_code, 400)
        Ejecucion.objects.filter(pk=self.contra.pk).update(
            estado_solver=Ejecucion.EstadoSolver.INFEASIBLE,
        )
        self.assertEqual(
            self.client.get(self.url, {"contra": self.contra.pk}).status_code, 409,
        )

    def test_aisla_ambos_ids_y_permite_lectura_a_viewer(self):
        viewer, otro_workspace = crear_workspace_prueba()
        WorkspaceMembership.objects.create(
            workspace=self.workspace, usuario=viewer, rol=WorkspaceMembership.Rol.VIEWER,
        )
        self.client.force_authenticate(viewer)
        self.assertEqual(self.client.get(self.url, {"contra": self.contra.pk}).status_code, 200)
        problema_externo = Problema.objects.create(workspace=otro_workspace, nombre="Externo")
        externa = self.crear_ejecucion(problema_externo, "0.00")
        self.assertEqual(self.client.get(self.url, {"contra": externa.pk}).status_code, 404)
        url_externa = f"/api/ejecuciones/{externa.pk}/comparar/"
        self.assertEqual(self.client.get(url_externa, {"contra": self.base.pk}).status_code, 404)

    def test_openapi_documenta_ruta_y_parametros(self):
        respuesta = self.client.get("/api/schema/")
        operacion = respuesta.data["paths"]["/api/ejecuciones/{id}/comparar/"]["get"]
        self.assertEqual(
            {p["name"] for p in operacion["parameters"]},
            {"id", "contra", "X-Workspace-ID"},
        )
