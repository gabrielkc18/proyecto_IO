
from apps.optimizacion.models import Ejecucion
from apps.resultados.models import (
    ResultadoProducto,
    ResultadoRecurso,
)


def construir_contexto(ejecucion_id):
    """
    Recupera una ejecución y construye el contexto
    estructurado que recibirá el modelo de IA.
    """

    try:
        ejecucion = Ejecucion.objects.select_related(
            "problema"
        ).get(pk=ejecucion_id)

    except Ejecucion.DoesNotExist:
        raise ValueError(
            "La ejecución solicitada no existe."
        )

    if ejecucion.estado_proceso != Ejecucion.EstadoProceso.TERMINADO:
        raise ValueError(
            "No se puede analizar una ejecución que no haya terminado."
        )

    productos = ResultadoProducto.objects.filter(
        ejecucion=ejecucion
    ).order_by("nombre_producto")

    recursos = ResultadoRecurso.objects.filter(
        ejecucion=ejecucion
    ).order_by("nombre_recurso")

    contexto = {
        "problema": {
            "id": ejecucion.problema_id,
            "nombre": ejecucion.problema.nombre,
            "sentido_objetivo": ejecucion.problema.sentido_objetivo,
        },
        "ejecucion": {
            "id": ejecucion.id,
            "estado_proceso": ejecucion.estado_proceso,
            "estado_solver": ejecucion.estado_solver,
            "utilidad_total": (
                str(ejecucion.utilidad_total)
                if ejecucion.utilidad_total is not None
                else None
            ),
            "solver": ejecucion.solver_nombre,
        },
        "productos": [
            {
                "nombre": producto.nombre_producto,
                "utilidad_unitaria": str(
                    producto.utilidad_unitaria
                ),
                "cantidad_producida": producto.cantidad,
                "utilidad_aportada": str(
                    producto.utilidad_aportada
                ),
            }
            for producto in productos
        ],
        "recursos": [
            {
                "nombre": recurso.nombre_recurso,
                "unidad_medida": recurso.unidad_medida,
                "disponibilidad": str(recurso.disponibilidad),
                "consumo_total": str(recurso.consumo_total),
                "holgura": str(recurso.holgura),
                "estado_uso": recurso.estado_uso,
            }
            for recurso in recursos
        ],
        "snapshot_entrada": ejecucion.snapshot_entrada,
    }

    return contexto
