"""Comparacion entre escenario base y solucion optima (generico n productos, m recursos)."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def _tol() -> float:
    return 1e-9


def _evaluar_escenario(datos: Dict[str, Any], produccion: Dict[str, float]) -> Tuple[bool, float, List[Dict[str, Any]], List[str]]:
    productos = {p.get("id"): p for p in (datos.get("PRODUCTO", []) or [])}
    recursos = list(datos.get("RECURSO", []) or [])
    consumos = dict(datos.get("CONSUMO_RECURSO", {}) or {})
    restricciones_extra = list(datos.get("RESTRICCIONES_ADICIONALES", []) or [])
    produccion = produccion or {}

    utilidad = 0.0
    for pid, cantidad in produccion.items():
        utilidad += float(productos.get(pid, {}).get("utilidad_unitaria", 0.0) or 0.0) * float(cantidad or 0.0)

    detalle_restricciones: List[Dict[str, Any]] = []
    motivos: List[str] = []
    factible = True
    tol = _tol()

    # Restricciones de recursos (<=)
    for r in recursos:
        rid = r.get("id")
        disponibilidad = float(r.get("disponibilidad", 0.0) or 0.0)
        uso = 0.0
        fila = consumos.get(rid, {}) or {}
        for pid, cantidad in produccion.items():
            uso += float(fila.get(pid, 0.0) or 0.0) * float(cantidad or 0.0)
        holgura = disponibilidad - uso
        viola = holgura < -tol
        if viola:
            factible = False
            exceso = abs(holgura)
            unidad = r.get("unidad") or "unidades"
            motivos.append(
                f"Recurso {r.get('nombre', rid)} ({rid}): requiere {uso:.6g} {unidad} y dispone {disponibilidad:.6g} {unidad} (exceso {exceso:.6g})."
            )
        detalle_restricciones.append(
            {
                "restriccion_id": f"R_{rid}",
                "recurso_id": rid,
                "nombre": r.get("nombre", rid),
                "tipo": "recurso",
                "sentido": "<=",
                "valor_derecho": disponibilidad,
                "consumo_total": uso,
                "holgura": holgura,
                "estado_recurso": "VIOLADO" if viola else ("AGOTADO" if abs(holgura) <= tol else "CON_HOLGURA"),
                **({"unidad": r.get("unidad")} if r.get("unidad") is not None else {}),
            }
        )

    # Restricciones adicionales
    for i, extra in enumerate(restricciones_extra):
        rid = extra.get("id") or extra.get("restriccion_id") or f"EXTRA_{i+1}"
        sentido = str(extra.get("sentido", "<="))
        rhs = float(extra.get("valor_derecho", 0.0) or 0.0)
        coefs = extra.get("coeficientes", {}) or {}
        lhs = 0.0
        for pid, cantidad in produccion.items():
            lhs += float(coefs.get(pid, 0.0) or 0.0) * float(cantidad or 0.0)
        if sentido == "<=":
            holgura = rhs - lhs
            viola = holgura < -tol
        elif sentido == ">=":
            holgura = lhs - rhs
            viola = holgura < -tol
        else:  # ==
            holgura = 0.0
            viola = abs(lhs - rhs) > tol
            holgura = rhs - lhs
        if viola:
            factible = False
            motivos.append(
                f"Restriccion {extra.get('nombre', rid)} ({rid}): {lhs:.6g} {sentido} {rhs:.6g} no se cumple."
            )
        detalle_restricciones.append(
            {
                "restriccion_id": rid,
                "nombre": extra.get("nombre", rid),
                "tipo": "adicional",
                "sentido": sentido,
                "valor_derecho": rhs,
                "consumo_total": lhs,
                "holgura": holgura,
                "estado_recurso": "VIOLADO" if viola else "ACTIVA",
            }
        )

    return factible, utilidad, detalle_restricciones, motivos


def comparar_escenarios(datos: Dict[str, Any], resultado_optimo: Dict[str, Any]) -> Dict[str, Any]:
    """Evalua el escenario base y compara contra el optimo solo si es valido hacerlo."""
    escenario = datos.get("ESCENARIO_BASE", {}) or {}
    produccion_base = escenario.get("produccion", {}) or {}
    utilidad_reportada = float(escenario.get("utilidad_reportada_enunciado", 0.0) or 0.0)
    factible_base, utilidad_base_calculada, detalle_base, motivos = _evaluar_escenario(datos, produccion_base)

    optimo_ok = (resultado_optimo.get("EJECUCION", {}) or {}).get("estado_proceso") == "OPTIMO"
    utilidad_optima = resultado_optimo.get("utilidad_total") if optimo_ok else None

    comparacion = {
        "comparacion_valida": False,
        "incremento_absoluto": None,
        "incremento_porcentual": None,
        "referencia_incremento": None,
        "motivo_no_comparacion": None,
        "incremento_absoluto_vs_enunciado": None,
        "incremento_porcentual_vs_enunciado": None,
    }

    if not optimo_ok:
        comparacion["motivo_no_comparacion"] = "No existe solucion optima valida para realizar la comparacion."
    elif not factible_base:
        comparacion["motivo_no_comparacion"] = "El escenario base es infactible; no se calcula porcentaje de mejora frente a una referencia no ejecutable."
    elif utilidad_base_calculada == 0:
        comparacion["motivo_no_comparacion"] = "La utilidad base calculada es cero; no se puede calcular un porcentaje de mejora significativo."
    else:
        comparacion["comparacion_valida"] = True
        comparacion["referencia_incremento"] = "utilidad_base_calculada"
        comparacion["incremento_absoluto"] = float(utilidad_optima) - float(utilidad_base_calculada)
        comparacion["incremento_porcentual"] = (comparacion["incremento_absoluto"] / float(utilidad_base_calculada)) * 100.0

    # produccion optima generica
    prod_opt = {}
    for item in (resultado_optimo.get("RESULTADO_PRODUCTO") or resultado_optimo.get("RESULTADO_VARIABLES") or []):
        pid = item.get("producto_id", item.get("variable_id"))
        prod_opt[pid] = item.get("cantidad_producir", item.get("valor"))

    return {
        "escenario_base": {
            "descripcion": escenario.get("descripcion", "Escenario base"),
            "produccion": produccion_base,
            "utilidad_reportada_enunciado": utilidad_reportada,
            "utilidad_calculada": utilidad_base_calculada,
            "diferencia_utilidad_reportada_vs_calculada": utilidad_reportada - utilidad_base_calculada,
            "es_factible": factible_base,
            "infactibilidad_demostrada": not factible_base,
            "motivos_no_factibilidad": motivos,
            "detalle_recursos": detalle_base,
        },
        "escenario_optimo": {
            "utilidad_total": utilidad_optima,
            "produccion": prod_opt,
            "estado_proceso": (resultado_optimo.get("EJECUCION", {}) or {}).get("estado_proceso"),
        },
        "comparacion": comparacion,
    }
