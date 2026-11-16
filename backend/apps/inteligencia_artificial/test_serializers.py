
from django.test import SimpleTestCase

from apps.inteligencia_artificial.serializers import AnalisisIASerializer


class AnalisisIASerializerTests(SimpleTestCase):

    def test_todos_los_campos_son_solo_lectura(self):
        serializer = AnalisisIASerializer()

        for nombre, campo in serializer.fields.items():
            with self.subTest(campo=nombre):
                self.assertTrue(campo.read_only)

    def test_no_acepta_datos_para_escritura(self):
        data = {
            "ejecucion": 1,
            "tipo_analisis": "GENERAL",
            "pregunta": "¿Qué indican los resultados?",
            "contenido": "La producción es óptima.",
            "modelo_ia": "modelo-prueba",
            "contexto_enviado": {
                "utilidad_total": 15000
            }
        }

        serializer = AnalisisIASerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data, {})
