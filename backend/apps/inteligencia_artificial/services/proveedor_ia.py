
import logging

from decouple import config
from django.conf import settings
from groq import APIConnectionError, APIStatusError, APITimeoutError, Groq


logger = logging.getLogger(__name__)


class ErrorProveedorIA(Exception):
    """Error controlado durante la comunicación con el proveedor."""


def generar_respuesta(mensajes, max_completion_tokens=1500):

    api_key = config("GROQ_API_KEY", default="")
    modelo = config(
        "GROQ_MODEL",
        default="openai/gpt-oss-120b",
    )

    if not api_key:
        raise ErrorProveedorIA(
            "La API Key de Groq no está configurada."
        )

    if not isinstance(mensajes, list) or not mensajes:
        raise ValueError(
            "Debe proporcionarse una lista de mensajes."
        )

    try:
        cliente = Groq(
            api_key=api_key,
            timeout=settings.GROQ_TIMEOUT_SECONDS,
            max_retries=0,
        )

        respuesta = cliente.chat.completions.create(
            model=modelo,
            messages=mensajes,
            max_completion_tokens=max_completion_tokens,
        )
    except (APIConnectionError, APIStatusError, APITimeoutError) as error:
        logger.warning(
            "La solicitud a Groq falló (%s).",
            type(error).__name__,
        )
        raise ErrorProveedorIA(
            "No fue posible comunicarse con el proveedor de IA."
        ) from error

    try:
        choice = respuesta.choices[0]
        contenido = choice.message.content
        modelo_respuesta = respuesta.model
    except (AttributeError, IndexError, TypeError) as error:
        raise ErrorProveedorIA(
            "El proveedor devolvió una respuesta inválida."
        ) from error

    if not isinstance(contenido, str) or not contenido.strip():
        raise ErrorProveedorIA(
            "El proveedor no devolvió contenido."
        )

    return {
        "contenido": contenido,
        "modelo": modelo_respuesta,
    }
