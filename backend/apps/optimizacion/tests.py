
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError

from apps.problemas.models import Problema
from apps.optimizacion.models import Ejecucion


class EjecucionModelTest(TestCase):

    def setUp(self):
        self.problema = Problema.objects.create(
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
