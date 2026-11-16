
from django.test import TestCase
from django.core.exceptions import ValidationError

from apps.problemas.models import Problema


class ProblemaModelTest(TestCase):

    def test_crear_problema_correctamente(self):
        problema = Problema.objects.create(
            nombre="Producción noviembre",
            descripcion="Escenario de producción"
        )

        self.assertEqual(problema.nombre, "Producción noviembre")
        self.assertEqual(problema.estado, "BORRADOR")
        self.assertEqual(problema.sentido_objetivo, "MAXIMIZAR")
        self.assertIsNotNone(problema.fecha_creacion)

    def test_nombre_debe_ser_unico(self):
        Problema.objects.create(
            nombre="Producción noviembre"
        )

        duplicado = Problema(
            nombre="Producción noviembre"
        )

        with self.assertRaises(ValidationError):
            duplicado.full_clean()

    def test_sentido_objetivo_debe_ser_valido(self):
        problema = Problema(
            nombre="Producción diciembre",
            sentido_objetivo="ALEATORIO"
        )

        with self.assertRaises(ValidationError):
            problema.full_clean()

    def test_estado_debe_ser_valido(self):
        problema = Problema(
            nombre="Producción enero",
            estado="INEXISTENTE"
        )

        with self.assertRaises(ValidationError):
            problema.full_clean()
