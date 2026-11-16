
from django.test import SimpleTestCase

from apps.resultados.serializers import (
    ResultadoProductoSerializer,
    ResultadoRecursoSerializer
)


class ResultadoProductoSerializerTests(SimpleTestCase):

    def test_todos_los_campos_son_solo_lectura(self):
        serializer = ResultadoProductoSerializer()

        for nombre, campo in serializer.fields.items():
            with self.subTest(campo=nombre):
                self.assertTrue(campo.read_only)

    def test_no_acepta_datos_para_escritura(self):
        data = {
            "ejecucion": 1,
            "producto": 1,
            "nombre_producto": "Producto 1",
            "cantidad": 100,
            "utilidad_aportada": "8000.00"
        }

        serializer = ResultadoProductoSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data, {})


class ResultadoRecursoSerializerTests(SimpleTestCase):

    def test_todos_los_campos_son_solo_lectura(self):
        serializer = ResultadoRecursoSerializer()

        for nombre, campo in serializer.fields.items():
            with self.subTest(campo=nombre):
                self.assertTrue(campo.read_only)

    def test_no_acepta_datos_para_escritura(self):
        data = {
            "ejecucion": 1,
            "recurso": 1,
            "nombre_recurso": "Materia prima A",
            "disponibilidad": "3000.00",
            "consumo_total": "2500.00",
            "holgura": "500.00",
            "estado_uso": "CON_HOLGURA"
        }

        serializer = ResultadoRecursoSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data, {})
