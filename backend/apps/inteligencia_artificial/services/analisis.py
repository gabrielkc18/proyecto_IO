
import json

from django.db import transaction

from apps.optimizacion.models import Ejecucion
from apps.inteligencia_artificial.models import AnalisisIA

from apps.inteligencia_artificial.services.contexto import (
    construir_contexto,
)

from apps.inteligencia_artificial.services.proveedor_ia import (
    generar_respuesta,
)


def generar_analisis(ejecucion_id, pregunta=""):
    """
    Genera un análisis de IA sobre una ejecución óptima
    y almacena el resultado en AnalisisIA.
    """

    try:
        ejecucion = Ejecucion.objects.get(pk=ejecucion_id)
    except Ejecucion.DoesNotExist:
        raise ValueError("La ejecución solicitada no existe.")

    if ejecucion.estado_proceso != Ejecucion.EstadoProceso.TERMINADO:
        raise ValueError("La ejecución todavía no ha terminado.")

    if ejecucion.estado_solver != Ejecucion.EstadoSolver.OPTIMAL:
        raise ValueError(
            "Solo se pueden analizar ejecuciones con solución óptima."
        )

    contexto = construir_contexto(ejecucion_id)

    contexto_json = json.dumps(
        contexto,
        ensure_ascii=False,
        indent=2,
    )

    instrucciones = """
    Eres un analista especializado en investigación de operaciones,
    programación lineal y planificación de producción industrial.

    Tu función es interpretar los resultados de una optimización
    matemática que ya fue calculada por un solver.

    REGLAS OBLIGATORIAS:

    1. Utiliza exclusivamente los datos proporcionados.
    2. No inventes cantidades, utilidades, disponibilidades ni consumos.
    3. No modifiques ni recalcules la solución del solver.
    4. Diferencia claramente los datos comprobados de tus interpretaciones.
    5. No afirmes que una holgura cero implica necesariamente
       un precio sombra distinto de cero.
    6. No inventes precios sombra ni valores duales.
    7. Si faltan datos para una conclusión, indícalo.
    8. Responde en español, con lenguaje técnico pero comprensible.
    9. Organiza el análisis con títulos y conclusiones.
    """

    solicitud = f"""
    Analiza la siguiente ejecución de optimización.

    DATOS DE LA EJECUCIÓN:

    {contexto_json}

    PREGUNTA DEL USUARIO:

    {pregunta if pregunta else "Realiza un análisis general de los resultados."}

    Explica el resultado, la producción obtenida, la utilidad,
    el aprovechamiento de los recursos y las conclusiones
    que puedan extraerse de los datos.
    """

    respuesta = generar_respuesta(
        mensajes=[
            {
                "role": "system",
                "content": instrucciones,
            },
            {
                "role": "user",
                "content": solicitud,
            },
        ],
        max_completion_tokens=2000,
    )

    with transaction.atomic():
        analisis = AnalisisIA.objects.create(
            ejecucion=ejecucion,
            tipo_analisis="ANALISIS_GENERAL",
            pregunta=pregunta,
            contenido=respuesta["contenido"],
            modelo_ia=respuesta["modelo"],
            contexto_enviado=contexto,
        )

    return analisis
