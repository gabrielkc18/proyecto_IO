
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError

from apps.problemas.models import Problema
from apps.optimizacion.models import Ejecucion


from django.test import SimpleTestCase
from apps.optimizacion.services.solver import resolver_problema
from apps.workspaces.test_utils import crear_workspace_prueba


class EjecucionModelTest(TestCase):

    def setUp(self):
        self.usuario, self.workspace = crear_workspace_prueba()
        self.problema = Problema.objects.create(
            workspace=self.workspace,
            nombre="Producción noviembre"
        )

    def test_crear_ejecucion_correctamente(self):
        ejecucion = Ejecucion.objects.create(
            problema=self.problema,
            snapshot_entrada={
                "sentido_objetivo": "MAXIMIZAR",
                "productos": [],
                "recursos": []
            }
        )

        self.assertEqual(ejecucion.problema, self.problema)
        self.assertEqual(ejecucion.estado_proceso, "PENDIENTE")
        self.assertIsNone(ejecucion.estado_solver)
        self.assertIsNone(ejecucion.fecha_fin)
        self.assertIsNotNone(ejecucion.fecha_inicio)

    def test_estado_proceso_debe_ser_valido(self):
        ejecucion = Ejecucion(
            problema=self.problema,
            estado_proceso="INVALIDO"
        )

        with self.assertRaises(ValidationError):
            ejecucion.full_clean()

    def test_estado_solver_debe_ser_valido(self):
        ejecucion = Ejecucion(
            problema=self.problema,
            estado_solver="INVALIDO"
        )

        with self.assertRaises(ValidationError):
            ejecucion.full_clean()

    def test_snapshot_almacena_datos_json(self):
        snapshot = {
            "sentido_objetivo": "MAXIMIZAR",
            "productos": [
                {"codigo": "P1", "utilidad": 80}
            ],
            "recursos": [
                {"nombre": "Materia A", "disponibilidad": 3000}
            ]
        }

        ejecucion = Ejecucion.objects.create(
            problema=self.problema,
            snapshot_entrada=snapshot
        )

        ejecucion_recuperada = Ejecucion.objects.get(
            pk=ejecucion.pk
        )

        self.assertEqual(
            ejecucion_recuperada.snapshot_entrada,
            snapshot
        )

    def test_no_permite_eliminar_problema_con_ejecuciones(self):
        Ejecucion.objects.create(
            problema=self.problema
        )

        with self.assertRaises(ProtectedError):
            self.problema.delete()

class SolverTest(SimpleTestCase):

    def setUp(self):
        self.productos = [
            {"codigo": "P1", "utilidad_unitaria": 5},
            {"codigo": "P2", "utilidad_unitaria": 8},
        ]

        self.recursos = [
            {
                "nombre": "Materia A",
                "disponibilidad": 10,
                "consumos": {"P1": 2, "P2": 4},
            }
        ]

    def test_resolver_modelo_optimo(self):
        resultado = resolver_problema(
            self.productos,
            self.recursos,
            "MAX"
        )

        self.assertEqual(resultado["estado"], "Optimal")
        self.assertEqual(resultado["utilidad_total"], 25)

        cantidades = {
            p["codigo"]: p["cantidad"]
            for p in resultado["productos"]
        }

        self.assertEqual(cantidades["P1"], 5)
        self.assertEqual(cantidades["P2"], 0)

    def test_calcular_consumo_y_holgura(self):
        resultado = resolver_problema(
            self.productos,
            self.recursos,
            "MAX"
        )

        recurso = resultado["recursos"][0]

        self.assertEqual(recurso["consumo_total"], 10)
        self.assertEqual(recurso["holgura"], 0)
        self.assertEqual(recurso["estado_uso"], "AGOTADO")

    def test_rechazar_productos_vacios(self):
        with self.assertRaises(ValueError):
            resolver_problema([], self.recursos)

    def test_rechazar_recursos_vacios(self):
        with self.assertRaises(ValueError):
            resolver_problema(self.productos, [])

    def test_rechazar_sentido_invalido(self):
        with self.assertRaises(ValueError):
            resolver_problema(
                self.productos,
                self.recursos,
                "OTRO"
            )

    def test_rechazar_utilidad_negativa(self):
        productos = [
            {"codigo": "P1", "utilidad_unitaria": -5}
        ]

        with self.assertRaises(ValueError):
            resolver_problema(productos, self.recursos)

    def test_rechazar_disponibilidad_negativa(self):
        recursos = [
            {
                "nombre": "Materia A",
                "disponibilidad": -10,
                "consumos": {"P1": 2, "P2": 4},
            }
        ]

        with self.assertRaises(ValueError):
            resolver_problema(self.productos, recursos)

    def test_rechazar_codigos_duplicados(self):
        productos = [
            {"codigo": "P1", "utilidad_unitaria": 5},
            {"codigo": "P1", "utilidad_unitaria": 8},
        ]

        with self.assertRaises(ValueError):
            resolver_problema(productos, self.recursos)

    def test_rechazar_consumos_negativos(self):
        recursos = [
            {
                "nombre": "Materia A",
                "disponibilidad": 10,
                "consumos": {"P1": -1},
            }
        ]

        with self.assertRaisesRegex(ValueError, "consumos no pueden ser negativos"):
            resolver_problema(self.productos, recursos)

    def test_modelo_no_acotado_devuelve_estado_sin_fabricar_resultados(self):
        productos = [{"codigo": "P1", "utilidad_unitaria": 5}]
        recursos = [
            {
                "nombre": "Materia A",
                "disponibilidad": 10,
                "consumos": {"P1": 0},
            }
        ]

        resultado = resolver_problema(productos, recursos, "MAX", time_limit=5)

        self.assertEqual(resultado["estado"], "Unbounded")
        self.assertIsNone(resultado["utilidad_total"])
        self.assertEqual(resultado["productos"], [])
        self.assertEqual(resultado["recursos"], [])

    def test_timeout_del_solver_retorna_estado_no_resuelto(self):
        with (
            patch(
                "apps.optimizacion.services.solver.pulp.COIN_CMD",
            ) as solver_factory,
            patch(
                "apps.optimizacion.services.solver.pulp.LpProblem.solve",
                return_value=SimpleNamespace(status_str="Not Solved"),
            ) as solve,
        ):
            resultado = resolver_problema(
                self.productos,
                self.recursos,
                "MAX",
                time_limit=7,
            )

        solver_factory.assert_called_once_with(msg=False, timeLimit=7)
        solve.assert_called_once_with(solver_factory.return_value)
        self.assertEqual(resultado["estado"], "Not Solved")
        self.assertIsNone(resultado["utilidad_total"])
        self.assertEqual(resultado["productos"], [])
