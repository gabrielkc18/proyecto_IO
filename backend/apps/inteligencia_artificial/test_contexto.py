
from decimal import Decimal

from django.test import TestCase

from apps.problemas.models import Problema
from apps.productos.models import Producto
from apps.recursos.models import Recurso, ConsumoRecurso
from apps.optimizacion.services.ejecucion import ejecutar_optimizacion
from apps.inteligencia_artificial.services.contexto import (
    construir_contexto,
)
from apps.workspaces.test_utils import crear_workspace_prueba


class ContextoIATests(TestCase):

    def setUp(self):
        self.usuario, self.workspace = crear_workspace_prueba()
        self.problema = Problema.objects.create(
            workspace=self.workspace,
            nombre="Problema contexto IA",
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

    def test_construye_contexto_de_ejecucion_optima(self):
        ejecucion = ejecutar_optimizacion(self.problema.id)
        self.problema.nombre = "Nombre actual"
        self.problema.sentido_objetivo = Problema.SentidoObjetivo.MINIMIZAR
        self.problema.save(update_fields=["nombre", "sentido_objetivo"])

        contexto = construir_contexto(ejecucion.id)

        self.assertEqual(
            contexto["problema"]["nombre"],
            "Problema contexto IA",
        )
        self.assertEqual(contexto["problema"]["sentido_objetivo"], "MAXIMIZAR")

        self.assertEqual(
            contexto["ejecucion"]["estado_solver"],
            "Optimal",
        )

        self.assertEqual(
            contexto["ejecucion"]["utilidad_total"],
            "25.00",
        )

        self.assertEqual(
            contexto["productos"][0]["cantidad_producida"],
            5,
        )

        self.assertEqual(
            contexto["recursos"][0]["holgura"],
            "0.00",
        )

        self.assertIn("snapshot_entrada", contexto)

    def test_ejecucion_inexistente_genera_error(self):
        with self.assertRaises(ValueError):
            construir_contexto(99999)

    def test_ejecucion_no_terminada_genera_error(self):
        from apps.optimizacion.models import Ejecucion

        ejecucion = Ejecucion.objects.create(
            problema=self.problema,
            estado_proceso=Ejecucion.EstadoProceso.PENDIENTE,
            solver_nombre="CBC",
            snapshot_entrada={},
        )

        with self.assertRaises(ValueError):
            construir_contexto(ejecucion.id)
