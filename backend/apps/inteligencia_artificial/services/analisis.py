
import hashlib
import json
import logging

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.optimizacion.models import Ejecucion
from apps.inteligencia_artificial.models import (
    AnalisisIA,
    SolicitudAnalisisIA,
)

from apps.inteligencia_artificial.services.contexto import (
    construir_contexto,
)

from apps.inteligencia_artificial.services.proveedor_ia import (
    generar_respuesta,
)


CONSENTIMIENTO_VERSION = "ai-disclosure-v1"
logger = logging.getLogger(__name__)


class ConflictoIdempotencia(Exception):
    pass


def recuperar_analisis(solicitud, ejecucion_id, pregunta):
    if solicitud.ejecucion_id != ejecucion_id:
        raise ConflictoIdempotencia(
            "La clave Idempotency-Key ya se usó con otros datos."
        )

    if solicitud.estado == SolicitudAnalisisIA.Estado.COMPLETED and solicitud.analisis_id:
        analisis = solicitud.analisis
        if analisis.pregunta == pregunta:
            return analisis, True
        raise ConflictoIdempotencia(
            "La clave Idempotency-Key ya se usó con otros datos."
        )

    raise ConflictoIdempotencia(
        "La solicitud ya fue recibida y no se repetirá. "
        "Usa una nueva Idempotency-Key para un nuevo intento."
    )


def marcar_solicitud_fallida(solicitud_id, error):
    with transaction.atomic():
        solicitud_ia = SolicitudAnalisisIA.objects.select_for_update().get(
            pk=solicitud_id,
        )
        solicitud_ia.estado = SolicitudAnalisisIA.Estado.FAILED
        solicitud_ia.save(update_fields=["estado", "fecha_actualizacion"])
    logger.error(
        "Falló una solicitud de análisis IA (%s) request_id=%s",
        type(error).__name__,
        solicitud_id,
    )


def minimizar_contexto(contexto):
    return {
        "sentido_objetivo": contexto["problema"]["sentido_objetivo"],
        "ejecucion": {
            "estado_solver": contexto["ejecucion"]["estado_solver"],
            "utilidad_total": contexto["ejecucion"]["utilidad_total"],
        },
        "productos": [
            {
                "producto": f"Producto {indice}",
                "utilidad_unitaria": producto["utilidad_unitaria"],
                "cantidad_producida": producto["cantidad_producida"],
                "utilidad_aportada": producto["utilidad_aportada"],
            }
            for indice, producto in enumerate(contexto["productos"], start=1)
        ],
        "recursos": [
            {
                "recurso": f"Recurso {indice}",
                "unidad_medida": recurso["unidad_medida"],
                "disponibilidad": recurso["disponibilidad"],
                "consumo_total": recurso["consumo_total"],
                "holgura": recurso["holgura"],
                "estado_uso": recurso["estado_uso"],
            }
            for indice, recurso in enumerate(contexto["recursos"], start=1)
        ],
    }


def generar_analisis(
    ejecucion_id,
    pregunta="",
    *,
    consentimiento_confirmado=False,
    solicitante,
    clave_idempotencia,
) -> tuple[AnalisisIA, bool]:
    """
    Genera un análisis de IA sobre una ejecución óptima
    y almacena el resultado en AnalisisIA.
    """

    if not consentimiento_confirmado:
        raise ValueError(
            "Se requiere consentimiento explícito para enviar datos a Groq."
        )

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

    solicitudes = SolicitudAnalisisIA.objects.filter(
        solicitante=solicitante,
        clave_idempotencia=clave_idempotencia,
    )
    solicitud_existente = solicitudes.select_related("analisis").first()
    if solicitud_existente is not None:
        return recuperar_analisis(solicitud_existente, ejecucion.pk, pregunta)

    contexto = minimizar_contexto(construir_contexto(ejecucion_id))
    huella = hashlib.sha256(
        json.dumps(
            {
                "ejecucion_id": ejecucion.pk,
                "pregunta": pregunta,
                "contexto": contexto,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    fecha_consentimiento = timezone.now()

    try:
        with transaction.atomic():
            solicitud_ia = SolicitudAnalisisIA.objects.create(
                ejecucion=ejecucion,
                solicitante=solicitante,
                clave_idempotencia=clave_idempotencia,
                huella_solicitud=huella,
                estado=SolicitudAnalisisIA.Estado.PROCESSING,
                consentimiento_confirmado=True,
                fecha_consentimiento=fecha_consentimiento,
                consentimiento_version=CONSENTIMIENTO_VERSION,
            )
    except IntegrityError:
        with transaction.atomic():
            solicitud_ia = solicitudes.select_for_update().first()
            if solicitud_ia is None:
                raise
            return recuperar_analisis(solicitud_ia, ejecucion.pk, pregunta)

    contexto_json = json.dumps(contexto, ensure_ascii=False, indent=2)

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

    try:
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
        contenido = respuesta["contenido"]
        modelo = respuesta["modelo"]
    except Exception as error:
        marcar_solicitud_fallida(solicitud_ia.pk, error)
        raise

    try:
        with transaction.atomic():
            solicitud_ia = SolicitudAnalisisIA.objects.select_for_update().get(
                pk=solicitud_ia.pk,
            )
            analisis = AnalisisIA.objects.create(
                ejecucion=ejecucion,
                tipo_analisis="ANALISIS_GENERAL",
                pregunta=pregunta,
                contenido=contenido,
                modelo_ia=modelo,
                contexto_enviado=contexto,
                consentimiento_confirmado=True,
                fecha_consentimiento=fecha_consentimiento,
                consentimiento_version=CONSENTIMIENTO_VERSION,
                solicitado_por=solicitante,
            )
            solicitud_ia.analisis = analisis
            solicitud_ia.estado = SolicitudAnalisisIA.Estado.COMPLETED
            solicitud_ia.save(
                update_fields=["analisis", "estado", "fecha_actualizacion"],
            )
    except Exception as error:
        marcar_solicitud_fallida(solicitud_ia.pk, error)
        raise

    return analisis, False
