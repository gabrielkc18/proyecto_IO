
from decouple import config
from groq import Groq


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
        cliente = Groq(api_key=api_key)

        respuesta = cliente.chat.completions.create(
            model=modelo,
            messages=mensajes,
            max_completion_tokens=max_completion_tokens,
        )

        contenido = respuesta.choices[0].message.content

        if not contenido:
            raise ErrorProveedorIA(
                "El proveedor no devolvió contenido."
            )

        return {
            "contenido": contenido,
            "modelo": respuesta.model,
        }

    except ErrorProveedorIA:
        raise

    except Exception as error:
        raise ErrorProveedorIA(
            "No fue posible comunicarse con el proveedor de IA."
        ) from error
