
from django.test import TestCase

from apps.problemas.models import Problema
from apps.problemas.serializers import ProblemaSerializer


class ProblemaSerializerTests(TestCase):

    def test_crear_problema_valido(self):
        data = {
            "nombre": "Producción industrial",
            "descripcion": "Optimización de producción",
            "sentido_objetivo": "MAXIMIZAR",
            "estado": "BORRADOR"
        }

        serializer = ProblemaSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_nombre_obligatorio(self):
        data = {
            "descripcion": "Problema sin nombre",
            "sentido_objetivo": "MAXIMIZAR",
            "estado": "BORRADOR"
        }

        serializer = ProblemaSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("nombre", serializer.errors)

    def test_nombre_unico(self):
        Problema.objects.create(
            nombre="Producción industrial"
        )

        data = {
            "nombre": "Producción industrial",
            "sentido_objetivo": "MAXIMIZAR",
            "estado": "BORRADOR"
        }

        serializer = ProblemaSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("nombre", serializer.errors)
