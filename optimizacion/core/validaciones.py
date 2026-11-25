"""Validaciones de integridad y construccion de snapshots de entrada."""

from __future__ import annotations

import copy
import json
import math
from typing import Any, Dict, List, Tuple

_SENSES = {"<=", ">=", "==", "=", "LE", "GE", "EQ"}
_SENSE_MAP = {"<=": "<=", "LE": "<=", ">=": ">=", "GE": ">=", "==": "==", "=": "==", "EQ": "=="}
_TIPOS_VAR = {"continuous", "integer", "binary", "CONTINUOUS", "INTEGER", "BINARY"}
_OBJ_SENTIDOS = {"max", "min", "maximizar", "minimizar", "MAX", "MIN", "MAXIMIZE", "MINIMIZE"}


def _es_numero_finito(valor: Any) -> bool:
    return isinstance(valor, (int, float)) and not isinstance(valor, bool) and math.isfinite(float(valor))


def _norm_sentido_obj(s: Any) -> str:
    t = str(s or "max").lower()
    return "min" if t in {"min", "minimizar", "minimize"} else "max"


def _norm_sentido_rest(s: Any) -> str:
    if s is None:
        return "<="
    return _SENSE_MAP.get(str(s), str(s))


def _norm_tipo_var(t: Any) -> str:
    x = str(t or "continuous").strip().lower()
    if x in {"integer", "int"}:
        return "integer"
    if x == "binary":
        return "binary"
    return "continuous"


def _obtener_config_generica(datos: Dict[str, Any]) -> Dict[str, Any] | None:
    """Normaliza formatos soportados a una configuracion generica interna."""
    if datos is None or not isinstance(datos, dict):
        return None

    if "VARIABLES" in datos and "FUNCION_OBJETIVO" in datos and "RESTRICCIONES" in datos:
        problema = dict(datos.get("PROBLEMA", {}) or {})
        variables = list(datos.get("VARIABLES", []) or [])
        fo = dict(datos.get("FUNCION_OBJETIVO", {}) or {})
        restricciones = list(datos.get("RESTRICCIONES", []) or [])
        return {
            "PROBLEMA": problema,
            "VARIABLES": variables,
            "FUNCION_OBJETIVO": fo,
            "RESTRICCIONES": restricciones,
            "ESCENARIO_BASE": datos.get("ESCENARIO_BASE"),
            "_origen": "generico",
        }

    if "PRODUCTO" in datos and "RECURSO" in datos and "CONSUMO_RECURSO" in datos:
        productos = list(datos.get("PRODUCTO", []) or [])
        recursos = list(datos.get("RECURSO", []) or [])
        consumos = dict(datos.get("CONSUMO_RECURSO", {}) or {})
        problema = dict(datos.get("PROBLEMA", {}) or {})
        objetivo = str(problema.get("objetivo", "maximizar")).lower()
        restricciones_extra = list(datos.get("RESTRICCIONES_ADICIONALES", []) or [])

        variables = []
        for p in productos:
            tipo = _norm_tipo_var(p.get("tipo_variable") or p.get("tipo") or "continuous")
            cota_inf = p.get("cota_inferior") if p.get("cota_inferior") is not None else p.get("limite_inferior")
            cota_sup = p.get("cota_superior") if p.get("cota_superior") is not None else p.get("limite_superior")
            if cota_inf is None:
                cota_inf = 0.0
            variables.append(
                {
                    "id": p.get("id"),
                    "nombre": p.get("nombre", p.get("id")),
                    "tipo": tipo,
                    "cota_inferior": cota_inf,
                    "cota_superior": cota_sup,
                }
            )
        restricciones = []
        for r in recursos:
            rid = r.get("id")
            restricciones.append(
                {
                    "id": f"R_{rid}" if rid is not None else None,
                    "nombre": r.get("nombre", rid),
                    "coeficientes": dict(consumos.get(rid, {}) or {}),
                    "sentido": "<=",
                    "valor_derecho": r.get("disponibilidad"),
                    "unidad": r.get("unidad"),
                    "recurso_id": rid,
                }
            )
        for i, extra in enumerate(restricciones_extra):
            e = dict(extra) if isinstance(extra, dict) else {}
            if not e.get("id"):
                e["id"] = f"EXTRA_{i+1}"
            restricciones.append(e)

        return {
            "PROBLEMA": problema,
            "VARIABLES": variables,
            "FUNCION_OBJETIVO": {
                "sentido": "min" if objetivo in {"min", "minimizar"} else "max",
                "coeficientes": {p.get("id"): p.get("utilidad_unitaria") for p in productos},
            },
            "RESTRICCIONES": restricciones,
            "ESCENARIO_BASE": datos.get("ESCENARIO_BASE"),
            "_origen": "compat",
            "_productos": productos,
            "_recursos": recursos,
            "_consumos": consumos,
            "_restricciones_extra": restricciones_extra,
        }

    return None


def validar_datos_modelo(datos: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Valida coherencia e integridad de la configuracion antes de optimizar."""
    errores: List[str] = []
    if not isinstance(datos, dict):
        return False, ["La configuracion del modelo debe ser un objeto/diccionario."]

    cfg = _obtener_config_generica(datos)
    if cfg is None:
        return False, ["Formato de configuracion no soportado. Se esperan VARIABLES/FUNCION_OBJETIVO/RESTRICCIONES o PRODUCTO/RECURSO/CONSUMO_RECURSO."]

    problema = cfg.get("PROBLEMA", {}) or {}
    variables = cfg.get("VARIABLES", []) or []
    fo = cfg.get("FUNCION_OBJETIVO", {}) or {}
    restricciones = cfg.get("RESTRICCIONES", []) or []

    if not variables:
        errores.append("No existen variables de decision definidas.")
    if not isinstance(variables, list):
        errores.append("VARIABLES debe ser una lista.")
        variables = []
    if not isinstance(restricciones, list):
        errores.append("RESTRICCIONES debe ser una lista.")
        restricciones = []

    sentido_obj = fo.get("sentido", problema.get("objetivo", "max"))
    if sentido_obj not in _OBJ_SENTIDOS:
        errores.append(f"Sentido de objetivo invalido: {sentido_obj}.")
    sentido_obj_n = _norm_sentido_obj(sentido_obj)
    coef_obj = fo.get("coeficientes", {})
    if not isinstance(coef_obj, dict):
        errores.append("FUNCION_OBJETIVO.coeficientes debe ser un objeto con coeficientes por variable.")
        coef_obj = {}

    ids_vars: List[Any] = []
    vars_por_id: Dict[Any, Dict[str, Any]] = {}
    for i, v in enumerate(variables):
        if not isinstance(v, dict):
            errores.append(f"Variable en posicion {i} tiene formato invalido.")
            continue
        vid = v.get("id")
        if vid is None or (isinstance(vid, str) and str(vid).strip() == ""):
            errores.append(f"Variable en posicion {i} tiene identificador vacio o ausente.")
            continue
        ids_vars.append(vid)
        vars_por_id[vid] = v
        tipo = v.get("tipo", "continuous")
        if tipo not in _TIPOS_VAR:
            errores.append(f"Tipo de variable invalido para {vid}: {tipo}.")
        lb = v.get("cota_inferior", 0.0)
        ub = v.get("cota_superior", 1.0 if _norm_tipo_var(tipo) == "binary" else None)
        if lb is not None and not _es_numero_finito(lb):
            errores.append(f"Cota inferior invalida para variable {vid}.")
        if ub is not None and not _es_numero_finito(ub):
            errores.append(f"Cota superior invalida para variable {vid}.")
        if _es_numero_finito(lb) and _es_numero_finito(ub) and float(lb) > float(ub):
            errores.append(f"La cota inferior de {vid} es mayor que la cota superior.")
        if _norm_tipo_var(tipo) == "binary":
            if lb is not None and _es_numero_finito(lb) and float(lb) < 0:
                errores.append(f"Variable binaria {vid} no puede tener cota inferior negativa.")
            if ub is not None and _es_numero_finito(ub) and float(ub) > 1:
                errores.append(f"Variable binaria {vid} no puede tener cota superior mayor que 1.")
        if vid in coef_obj and not _es_numero_finito(coef_obj.get(vid)):
            errores.append(f"Coeficiente de funcion objetivo invalido para variable {vid}.")

    if len(ids_vars) != len(set(ids_vars)):
        errores.append("Existen IDs de variables duplicados.")

    ids_restr = []
    for j, r in enumerate(restricciones):
        if not isinstance(r, dict):
            errores.append(f"Restriccion en posicion {j} tiene formato invalido.")
            continue
        rid = r.get("id") or r.get("recurso_id") or f"R{j+1}"
        if rid in ids_restr:
            errores.append(f"ID de restriccion duplicado: {rid}.")
        ids_restr.append(rid)
        sentido = _norm_sentido_rest(r.get("sentido", "<="))
        if sentido not in {"<=", ">=", "=="}:
            errores.append(f"Sentido invalido en restriccion {rid}: {r.get('sentido')}.")
        rhs = r.get("valor_derecho", r.get("disponibilidad"))
        if not _es_numero_finito(rhs):
            errores.append(f"Valor derecho invalido en restriccion {rid}.")
        elif "disponibilidad" in r and float(rhs) < 0:
            errores.append(f"Disponibilidad invalida o negativa para recurso {rid}.")
        coefs = r.get("coeficientes")
        if not isinstance(coefs, dict):
            errores.append(f"La restriccion {rid} no tiene una matriz/objeto de coeficientes valido.")
            continue
        es_recurso_compat = cfg.get("_origen") == "compat" and (str(rid).startswith("R_") or r.get("recurso_id") is not None)
        for vid in ids_vars:
            if vid not in coefs:
                if es_recurso_compat:
                    errores.append(f"Falta coeficiente de variable {vid} en restriccion {rid}.")
                else:
                    # en restricciones adicionales/genericas, coeficiente omitido se asume 0
                    continue
            else:
                val = coefs.get(vid)
                if not _es_numero_finito(val):
                    errores.append(f"Coeficiente invalido a_{{{rid},{vid}}}.")
                elif float(val) < 0 and es_recurso_compat:
                    errores.append(f"Consumo negativo o invalido a_{{{rid},{vid}}}={val}.")
        for vid in coefs.keys():
            if vid not in vars_por_id:
                errores.append(f"Restriccion {rid} referencia variable inexistente: {vid}.")

    # Validacion especifica formato producto/recurso (dinamica n x m)
    productos_in = datos.get("PRODUCTO") if isinstance(datos.get("PRODUCTO"), list) else (cfg.get("_productos") or [])
    recursos_in = datos.get("RECURSO") if isinstance(datos.get("RECURSO"), list) else (cfg.get("_recursos") or [])
    consumos_in = datos.get("CONSUMO_RECURSO") if isinstance(datos.get("CONSUMO_RECURSO"), dict) else (cfg.get("_consumos") or {})
    if isinstance(productos_in, list) and productos_in and isinstance(recursos_in, list):
        pids = [p.get("id") for p in productos_in if isinstance(p, dict)]
        rids = [r.get("id") for r in recursos_in if isinstance(r, dict)]
        if any(pid is None or (isinstance(pid, str) and str(pid).strip() == "") for pid in pids):
            errores.append("Existen identificadores de producto vacios.")
        if any(rid is None or (isinstance(rid, str) and str(rid).strip() == "") for rid in rids):
            errores.append("Existen identificadores de recurso vacios.")
        if len([pid for pid in pids if pid is not None]) != len(set([pid for pid in pids if pid is not None])):
            errores.append("Existen IDs de productos duplicados.")
        if len([rid for rid in rids if rid is not None]) != len(set([rid for rid in rids if rid is not None])):
            errores.append("Existen IDs de recursos duplicados.")
        for p in productos_in:
            if not isinstance(p, dict):
                continue
            pid = p.get("id", "<sin_id>")
            util = p.get("utilidad_unitaria")
            if util is not None and not _es_numero_finito(util):
                errores.append(f"Utilidad invalida para producto {pid}.")
            elif util is not None and float(util) < 0:
                errores.append(f"Utilidad invalida o negativa para producto {pid}.")
            c_inf = p.get("cota_inferior") if p.get("cota_inferior") is not None else p.get("limite_inferior")
            c_sup = p.get("cota_superior") if p.get("cota_superior") is not None else p.get("limite_superior")
            if c_inf is not None and not _es_numero_finito(c_inf):
                errores.append(f"Cota inferior invalida para producto {pid}.")
            if c_sup is not None and not _es_numero_finito(c_sup):
                errores.append(f"Cota superior invalida para producto {pid}.")
            if _es_numero_finito(c_inf) and _es_numero_finito(c_sup) and float(c_inf) > float(c_sup):
                errores.append(f"La cota inferior de {pid} es mayor que la cota superior.")
        for r in recursos_in:
            if not isinstance(r, dict):
                continue
            rid = r.get("id", "<sin_id>")
            disp = r.get("disponibilidad")
            if disp is not None and not _es_numero_finito(disp):
                errores.append(f"Disponibilidad invalida para recurso {rid}.")
            elif disp is not None and float(disp) < 0:
                errores.append(f"Disponibilidad invalida o negativa para recurso {rid}.")
        if isinstance(consumos_in, dict) and consumos_in:
            for rid in rids:
                if rid not in consumos_in:
                    errores.append(f"Falta la fila de consumos para el recurso {rid}.")
                    continue
                fila = consumos_in.get(rid, {})
                if not isinstance(fila, dict):
                    errores.append(f"Fila de consumos invalida para el recurso {rid}.")
                    continue
                for pid in pids:
                    if pid not in fila:
                        errores.append(f"Falta consumo a_{{{rid},{pid}}} en la matriz.")
                        continue
                    valc = fila.get(pid)
                    if not _es_numero_finito(valc):
                        errores.append(f"Consumo invalido a_{{{rid},{pid}}}.")
                    elif float(valc) < 0:
                        errores.append(f"Consumo negativo o invalido a_{{{rid},{pid}}}={valc}.")
                for pid_extra in fila.keys():
                    if pid_extra not in pids:
                        errores.append(f"Consumo referencia producto inexistente: {pid_extra} en recurso {rid}.")

    # Deteccion de posibles modelos no acotados (heuristica conservadora)
    if not errores and variables:
        for vid, v in vars_por_id.items():
            tipo = _norm_tipo_var(v.get("tipo"))
            if tipo == "binary":
                continue
            ub = v.get("cota_superior", 1.0 if tipo == "binary" else None)
            if ub is not None:
                continue
            cobj = float(coef_obj.get(vid, 0.0) or 0.0)
            if cobj == 0.0:
                continue
            mejora_si_sube = (sentido_obj_n == "max" and cobj > 0) or (sentido_obj_n == "min" and cobj < 0)
            if not mejora_si_sube:
                continue
            bloqueada = False
            for r in restricciones:
                sentido_r = _norm_sentido_rest(r.get("sentido", "<="))
                a = float((r.get("coeficientes") or {}).get(vid, 0.0) or 0.0)
                if a == 0.0:
                    continue
                if sentido_r == "<=" and a > 0:
                    bloqueada = True
                    break
                if sentido_r == ">=" and a < 0:
                    bloqueada = True
                    break
                if sentido_r == "==":
                    bloqueada = True
                    break
            if not bloqueada:
                errores.append(
                    f"Posible modelo no acotado: la variable {vid} mejora el objetivo al crecer y no tiene cota superior ni restricciones que limiten su aumento."
                )

    return (len(errores) == 0, errores)


def generar_snapshot_entrada(datos: Dict[str, Any]) -> Dict[str, Any]:
    """Genera un snapshot JSON-serializable de los datos de entrada."""
    snapshot = copy.deepcopy(datos)
    try:
        json.dumps(snapshot, ensure_ascii=False)
    except TypeError:
        snapshot = json.loads(json.dumps(snapshot, default=str, ensure_ascii=False))
    return snapshot
