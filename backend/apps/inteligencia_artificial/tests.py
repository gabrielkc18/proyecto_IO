
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError

from apps.problemas.models import Problema
from apps.optimizacion.models import Ejecucion
from .models import AnalisisIA


class AnalisisIATests(TestCase):

    def setUp(self):
        self.problema = Problema.objects.create(
            nombre="Problema de prueba"
        )

        self.ejecucion = Ejecucion.objects.create(
            problema=self.problema
        )

    def test_crear_analisis_ia_correctamente(self):
        analisis = AnalisisIA.objects.create(
            ejecucion=self.ejecucion,
            tipo_analisis="GENERAL",
            pregunta="¿Qué indican los resultados?",
            contenido="El análisis de los resultados indica...",
            modelo_ia="modelo-prueba",
            contexto_enviado={
                "utilidad_total": 15000,
                "productos": ["P1", "P2"]
            }
        )

        self.assertEqual(analisis.ejecucion, self.ejecucion)
        self.assertEqual(analisis.tipo_analisis, "GENERAL")

    def test_relacion_con_ejecucion(self):
        analisis = AnalisisIA.objects.create(
            ejecucion=self.ejecucion,
            tipo_analisis="GENERAL",
            contenido="Análisis de prueba",
            modelo_ia="modelo-prueba"
        )

        self.assertEqual(
            analisis.ejecucion_id,
            self.ejecucion.id
        )

    def test_contexto_json_se_persiste_correctamente(self):
        contexto = {
            "utilidad_total": 15000,
            "recursos": {
                "materia_prima": 3000,
                "horas_maquina": 1200
            }
        }

        analisis = AnalisisIA.objects.create(
            ejecucion=self.ejecucion,
            tipo_analisis="GENERAL",
            contenido="Análisis de prueba",
            modelo_ia="modelo-prueba",
            contexto_enviado=contexto
        )

        analisis_db = AnalisisIA.objects.get(pk=analisis.pk)

        self.assertEqual(analisis_db.contexto_enviado, contexto)

    def test_no_permitir_eliminar_ejecucion_con_analisis(self):
        AnalisisIA.objects.create(
            ejecucion=self.ejecucion,
            tipo_analisis="GENERAL",
            contenido="Análisis de prueba",
            modelo_ia="modelo-prueba"
        )

        with self.assertRaises(ProtectedError):
            self.ejecucion.delete()

