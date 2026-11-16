
from django.test import SimpleTestCase

from apps.optimizacion.serializers import EjecucionSerializer


class EjecucionSerializerTests(SimpleTestCase):

    def test_todos_los_campos_son_solo_lectura(self):
        serializer = EjecucionSerializer()

        for nombre, campo in serializer.fields.items():
            with self.subTest(campo=nombre):
                self.assertTrue(
                    campo.read_only,
                    f"El campo {nombre} debería ser de solo lectura."
                )

    def test_no_acepta_datos_para_escritura(self):
        data = {
            "problema": 1,
            "estado_proceso": "TERMINADO",
            "utilidad_total": "15000.00"
        }

        serializer = EjecucionSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data, {})
