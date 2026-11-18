from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings
from rest_framework.throttling import ScopedRateThrottle

from rest_framework.test import APITestCase
from rest_framework import status

from apps.problemas.models import Problema
from apps.productos.models import Producto
from apps.recursos.models import Recurso, ConsumoRecurso
from apps.optimizacion.models import Ejecucion
from apps.workspaces.test_utils import crear_workspace_prueba


@override_settings(CACHES={
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "ejecutar-optimizacion-api-tests",
    },
})
class EjecutarOptimizacionAPITests(APITestCase):

    def setUp(self):
        cache.clear()
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
            nombre="Problema API",
            sentido_objetivo=Problema.SentidoObjetivo.MAXIMIZAR,
            estado=Problema.Estado.LISTO,
        )

        self.producto = Producto.objects.create(
            problema=self.problema,
            codigo="P1",
            nombre="Producto 1",
            utilidad_unitaria=Decimal("5.00"),
        )

        self.recurso = Recurso.objects.create(
            problema=self.problema,
            nombre="Recurso A",
            unidad_medida="kg",
            disponibilidad=Decimal("10.00"),
        )

        ConsumoRecurso.objects.create(
            producto=self.producto,
            recurso=self.recurso,
            cantidad_por_unidad=Decimal("2.0000"),
        )

        self.url = f"/api/problemas/{self.problema.id}/ejecutar/"

    def test_problema_inexistente_responde_404(self):
        response = self.client.post(
            "/api/problemas/99999/ejecutar/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertEqual(Ejecucion.objects.count(), 0)

    def test_problema_borrador_responde_400(self):
        self.problema.estado = Problema.Estado.BORRADOR
        self.problema.save()

        response = self.client.post(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(Ejecucion.objects.count(), 0)

    def test_problema_listo_ejecuta_optimizacion(self):
        response = self.client.post(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(Ejecucion.objects.count(), 1)

        ejecucion = Ejecucion.objects.get()

        self.assertEqual(
            ejecucion.estado_proceso,
            Ejecucion.EstadoProceso.TERMINADO,
        )

        self.assertEqual(
            ejecucion.estado_solver,
            Ejecucion.EstadoSolver.OPTIMAL,
        )

        self.assertEqual(
            ejecucion.utilidad_total,
            Decimal("25.00"),
        )

        self.assertIn("id", response.data)

    def test_limite_por_usuario_impide_invocar_el_servicio(self):
        ejecucion = Ejecucion.objects.create(problema=self.problema)

        with (
            patch(
                "apps.optimizacion.views.ejecutar_optimizacion",
                return_value=ejecucion,
            ) as ejecutar,
            patch.object(
                ScopedRateThrottle,
                "timer",
                return_value=1000,
            ) as reloj,
        ):
            for _ in range(10):
                self.assertEqual(self.client.post(self.url).status_code, 201)

            respuesta = self.client.post(self.url)
            self.assertEqual(respuesta.status_code, 429)
            self.assertEqual(respuesta["Retry-After"], "3600")
            self.assertEqual(ejecutar.call_count, 10)
            self.assertEqual(Ejecucion.objects.count(), 1)

            reloj.return_value += 3600
            self.assertEqual(self.client.post(self.url).status_code, 201)
