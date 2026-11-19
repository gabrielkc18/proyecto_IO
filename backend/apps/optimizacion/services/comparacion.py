from apps.problemas.models import Problema
from apps.resultados.models import ResultadoProducto, ResultadoRecurso


def _sentido_historico(ejecucion):
    snapshot = ejecucion.snapshot_entrada
    sentido = snapshot.get("sentido_objetivo") if isinstance(snapshot, dict) else None
    return sentido if sentido in Problema.SentidoObjetivo.values else None


def _comparar_filas(modelo, campo_id, base, contra, metricas, unidad=None):
    resultados_base = {}
    resultados_contra = {}
    resultados = modelo.objects.filter(ejecucion_id__in=(base.pk, contra.pk))
    for resultado in resultados:
        destino = resultados_base if resultado.ejecucion_id == base.pk else resultados_contra
        destino[getattr(resultado, campo_id)] = resultado

    filas = []
    for identificador in sorted(resultados_base.keys() | resultados_contra.keys()):
        anterior = resultados_base.get(identificador)
        posterior = resultados_contra.get(identificador)
        delta = None
        if anterior is not None and posterior is not None:
            if unidad is None or getattr(anterior, unidad) == getattr(posterior, unidad):
                delta = {
                    campo: getattr(posterior, campo) - getattr(anterior, campo)
                    for campo in metricas
                }
        filas.append({
            campo_id: identificador,
            "base": anterior,
            "contra": posterior,
            "delta": delta,
        })
    return filas


def comparar_ejecuciones(base, contra):
    utilidad_delta = None
    if base.utilidad_total is not None and contra.utilidad_total is not None:
        utilidad_delta = contra.utilidad_total - base.utilidad_total

    return {
        "problema": base.problema_id,
        "base": {
            "id": base.pk,
            "sentido_objetivo": _sentido_historico(base),
            "utilidad_total": base.utilidad_total,
        },
        "contra": {
            "id": contra.pk,
            "sentido_objetivo": _sentido_historico(contra),
            "utilidad_total": contra.utilidad_total,
        },
        "delta_utilidad_total": utilidad_delta,
        "productos": _comparar_filas(
            ResultadoProducto, "producto_id", base, contra,
            ("cantidad", "utilidad_aportada"),
        ),
        "recursos": _comparar_filas(
            ResultadoRecurso, "recurso_id", base, contra,
            ("consumo_total", "holgura"), unidad="unidad_medida",
        ),
    }
