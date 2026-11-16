
from decouple import config
from groq import Groq


def generar_respuesta(
    mensajes,
    max_completion_tokens=1500,
):
    """
    Envía una conversación a Groq y devuelve
    el contenido generado y el modelo utilizado.
    """

    api_key = config("GROQ_API_KEY", default="")
    modelo = config(
        "GROQ_MODEL",
        default="openai/gpt-oss-120b",
    )

    if not api_key:
        raise ValueError(
            "La variable GROQ_API_KEY no está configurada."
        )

    if not isinstance(mensajes, list) or not mensajes:
        raise ValueError(
            "Debe proporcionarse una lista de mensajes."
        )

    cliente = Groq(api_key=api_key)

    respuesta = cliente.chat.completions.create(
        model=modelo,
        messages=mensajes,
        max_completion_tokens=max_completion_tokens,
    )

    contenido = respuesta.choices[0].message.content

    if not contenido:
        raise RuntimeError(
            "El proveedor de IA no devolvió contenido."
        )

    return {
        "contenido": contenido,
        "modelo": respuesta.model,
    }
