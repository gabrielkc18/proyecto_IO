"""Analisis de sensibilidad por escenarios (variacion configurable de disponibilidad/RHS)."""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional


def _resolver(datos: Dict[str, Any]) -> Dict[str, Any]:
    from optimizacion.core.motor_pulp import resolver_modelo
    return resolver_modelo(copy.deepcopy(datos))


def _normalizar_disponibilidad(valor: Any) -> float:
    v = float(valor)
    if abs(v) < 1e-9:
        v = 0.0
    return float(round(v + 0.0, 12))


def _resumen_resultado(res: Dict[str, Any]) -> Dict[str, Any]:
    recursos = {}
    for r in (res.get("RESULTADO_RECURSO") or res.get("RESULTADO_RESTRICCIONES") or []):
        rid = r.get("recurso_id") or r.get("restriccion_id")
        recursos[rid] = {
            "consumo_total": r.get("consumo_total", r.get("lado_izquierdo")),
            "holgura": r.get("holgura"),
            "estado_recurso": r.get("estado_recurso"),
        }
    produccion = {}
    for v in (res.get("RESULTADO_PRODUCTO") or res.get("RESULTADO_VARIABLES") or []):
        vid = v.get("producto_id", v.get("variable_id"))
        produccion[vid] = v.get("cantidad_producir", v.get("valor"))
    return {
        "valor_objetivo": res.get("valor_objetivo", res.get("utilidad_total")),
        "estado_proceso": (res.get("EJECUCION", {}) or {}).get("estado_proceso"),
        "recursos": recursos,
        "produccion": produccion,
    }


def _aplicar_rhs(datos_var: Dict[str, Any], objetivo_id: Any, nuevo_valor: float) -> None:
    for r in datos_var.get("RECURSO", []) or []:
        if r.get("id") == objetivo_id:
            r["disponibilidad"] = nuevo_valor
    for rest in datos_var.get("RESTRICCIONES_ADICIONALES", []) or []:
        rid_rest = rest.get("id", rest.get("restriccion_id"))
        if rid_rest == objetivo_id:
            rest["valor_derecho"] = nuevo_valor
    # formato generico
    for rest in datos_var.get("RESTRICCIONES", []) or []:
        rid_rest = rest.get("recurso_id", rest.get("id"))
        if rid_rest == objetivo_id or rest.get("id") == f"R_{objetivo_id}" or rest.get("id") == objetivo_id:
            rest["valor_derecho"] = nuevo_valor
            if "disponibilidad" in rest:
                rest["disponibilidad"] = nuevo_valor


def _objetivos_sensibilidad(datos: Dict[str, Any], seleccionados: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
    objs = []
    for r in (datos.get("RECURSO", []) or []):
        objs.append({"id": r.get("id"), "nombre": r.get("nombre", r.get("id")), "valor_derecho": r.get("disponibilidad", 0.0), "tipo": "recurso"})
    for e in (datos.get("RESTRICCIONES_ADICIONALES", []) or []):
        if str(e.get("sentido", "<=")) in {"<=", "LE"}:
            objs.append({"id": e.get("id", e.get("restriccion_id")), "nombre": e.get("nombre", e.get("id")), "valor_derecho": e.get("valor_derecho", 0.0), "tipo": "restriccion_adicional"})
    # formato generico sin RECURSO
    if not datos.get("RECURSO") and datos.get("RESTRICCIONES"):
        for rest in datos.get("RESTRICCIONES", []) or []:
            if str(rest.get("sentido", "<=")) in {"<=", "LE"}:
                rid = rest.get("recurso_id", rest.get("id"))
                objs.append({"id": rid, "nombre": rest.get("nombre", rid), "valor_derecho": rest.get("valor_derecho", 0.0), "tipo": "restriccion"})
    if seleccionados is not None:
        sel = set(seleccionados)
        objs = [o for o in objs if o.get("id") in sel]
    return objs


def analizar_sensibilidad_recursos(
    datos: Dict[str, Any],
    entero: bool = True,
    variacion_porcentaje: float = 10.0,
    variacion_absoluta: Optional[float] = None,
    objetivos: Optional[List[Any]] = None,
) -> Dict[str, Any]:
    """Ejecuta analisis de escenarios sobre recursos/restricciones seleccionadas.

    - Por defecto variacion porcentual ±10% (variacion_porcentaje=10).
    - Si se provee variacion_absoluta, se usa ±valor absoluto sobre el RHS.
    - Muestra impacto en Z y en cantidades de produccion x_p.
    - Aclara que es analisis por escenarios, no precios sombra duales.
    """
    _ = entero  # compatibilidad; tipos se respetan por variable en el motor
    base = _resolver(datos)
    utilidad_base = base.get("valor_objetivo", base.get("utilidad_total"))
    resumen_base = _resumen_resultado(base)
    resultados: List[Dict[str, Any]] = []
    impactos: List[Dict[str, Any]] = []

    objetivos_cfg = _objetivos_sensibilidad(datos, objetivos)
    for obj in objetivos_cfg:
        rid = obj.get("id")
        nombre = obj.get("nombre", rid)
        rhs_original = _normalizar_disponibilidad(obj.get("valor_derecho", 0.0))
        fila: Dict[str, Any] = {
            "recurso_id": rid,
            "recurso_nombre": nombre,
            "tipo_objetivo": obj.get("tipo"),
            "disponibilidad_original": rhs_original,
            "escenarios": {},
        }
        deltas_utilidad = []
        for etiqueta, signo in (("menos", -1.0), ("mas", 1.0)):
            if variacion_absoluta is not None:
                nuevo_rhs = _normalizar_disponibilidad(rhs_original + signo * float(variacion_absoluta))
                factor = None
            else:
                factor = 1.0 + signo * (float(variacion_porcentaje) / 100.0)
                nuevo_rhs = _normalizar_disponibilidad(rhs_original * factor)
            if nuevo_rhs < 0:
                nuevo_rhs = 0.0
            datos_var = copy.deepcopy(datos)
            _aplicar_rhs(datos_var, rid, nuevo_rhs)
            res = _resolver(datos_var)
            utilidad_var = res.get("valor_objetivo", res.get("utilidad_total"))
            delta = None
            if utilidad_base is not None and utilidad_var is not None:
                delta = float(utilidad_var) - float(utilidad_base)
                deltas_utilidad.append(abs(delta))
            resumen = _resumen_resultado(res)
            fila["escenarios"][etiqueta] = {
                "factor": factor,
                "variacion_absoluta": variacion_absoluta,
                "disponibilidad": nuevo_rhs,
                "utilidad_total": utilidad_var,
                "delta_utilidad": delta,
                "produccion": resumen["produccion"],
                "estado_proceso": (res.get("EJECUCION", {}) or {}).get("estado_proceso"),
                "recursos": resumen["recursos"],
            }
        impacto_promedio = sum(deltas_utilidad) / len(deltas_utilidad) if deltas_utilidad else None
        fila["impacto_promedio_abs"] = impacto_promedio
        impactos.append({"recurso_id": rid, "recurso_nombre": nombre, "impacto_promedio_abs": impacto_promedio})
        resultados.append(fila)

    impactos_validos = [i for i in impactos if i.get("impacto_promedio_abs") is not None]
    recurso_mas_impacto = max(impactos_validos, key=lambda x: x["impacto_promedio_abs"], default=None)
    var_desc = f"±{variacion_absoluta} (absoluto)" if variacion_absoluta is not None else f"±{variacion_porcentaje}%"

    return {
        "metodo": "analisis_escenarios_disponibilidad",
        "tipo_resultado": "escenarios",
        "interpretacion": "Analisis de sensibilidad por escenarios (variacion de disponibilidad/RHS) mostrando impacto en Z y en produccion x_p. No corresponde a precios sombra/valores duales.",
        "limitaciones": "Con variables enteras/binarias los cambios pueden ser no lineales y no deben interpretarse como valores duales; para precios sombra se requiere analisis dual de un modelo continuo apropiado.",
        "utilidad_base": utilidad_base,
        "produccion_base": resumen_base.get("produccion", {}),
        "variacion": var_desc,
        "resultados_por_recurso": resultados,
        "recurso_mayor_impacto": recurso_mas_impacto,
    }
