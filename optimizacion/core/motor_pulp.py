"""Motor generico de optimizacion con PuLP."""

from __future__ import annotations

import copy
import math
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import pulp
from pulp import constants as pulp_constants

from .validaciones import generar_snapshot_entrada, validar_datos_modelo

_TOL = 1e-9
_INT_TOL = 1e-7


def _estado_holgura(valor: float, tol: float = _TOL) -> str:
    if abs(valor) <= tol:
        return "AGOTADO"
    return "CON_HOLGURA" if valor > 0 else "VIOLADO"


def _norm_sentido_obj(s: Any) -> str:
    t = str(s or "max").lower()
    return "min" if t in {"min", "minimizar", "minimize"} else "max"


def _norm_sentido_rest(s: Any) -> str:
    mapa = {"<=": "<=", "LE": "<=", ">=": ">=", "GE": ">=", "==": "==", "=": "==", "EQ": "=="}
    return mapa.get(str(s), "<=")


def _norm_tipo_var(t: Any) -> str:
    x = str(t or "continuous").strip().lower()
    if x in {"integer", "int"}:
        return "integer"
    if x == "binary":
        return "binary"
    return "continuous"


def clasificar_modelo(tipos_decision: List[str]) -> str:
    """Clasifica el modelo segun las variables de decision de produccion."""
    tipos = [_norm_tipo_var(t) for t in tipos_decision]
    if not tipos:
        return "PL/LP"
    if all(t == "continuous" for t in tipos):
        return "PL/LP"
    if all(t in {"integer", "binary"} for t in tipos):
        return "PLE/IP"
    return "MILP"


def _normalizar_config(datos: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Convierte formatos soportados a configuracion interna generica.

    No fuerza tipos globales: cada variable conserva su tipo individual.
    """
    if not isinstance(datos, dict):
        return None

    if "VARIABLES" in datos and "FUNCION_OBJETIVO" in datos and "RESTRICCIONES" in datos:
        cfg = copy.deepcopy(datos)
        problema = dict(cfg.get("PROBLEMA", {}) or {})
        for v in cfg.get("VARIABLES", []) or []:
            v["id"] = v.get("id")
            v["nombre"] = v.get("nombre", v.get("id"))
            v["tipo"] = _norm_tipo_var(v.get("tipo"))
            if "cota_inferior" not in v or v.get("cota_inferior") is None:
                v["cota_inferior"] = 0.0
        cfg["PROBLEMA"] = problema
        cfg["_origen"] = "compat" if ("PRODUCTO" in datos and "RECURSO" in datos) else "generico"
        return cfg

    if "PRODUCTO" in datos and "RECURSO" in datos and "CONSUMO_RECURSO" in datos:
        productos = list(datos.get("PRODUCTO", []) or [])
        recursos = list(datos.get("RECURSO", []) or [])
        consumos = dict(datos.get("CONSUMO_RECURSO", {}) or {})
        problema = dict(datos.get("PROBLEMA", {}) or {})
        restricciones_extra = list(datos.get("RESTRICCIONES_ADICIONALES", []) or [])

        variables = []
        for p in productos:
            tipo_v = _norm_tipo_var(p.get("tipo_variable") or p.get("tipo") or "continuous")
            cota_inf = p.get("cota_inferior") if p.get("cota_inferior") is not None else p.get("limite_inferior")
            cota_sup = p.get("cota_superior") if p.get("cota_superior") is not None else p.get("limite_superior")
            if cota_inf is None:
                cota_inf = 0.0
            variables.append(
                {
                    "id": p.get("id"),
                    "nombre": p.get("nombre", p.get("id")),
                    "tipo": tipo_v,
                    "cota_inferior": cota_inf,
                    "cota_superior": cota_sup,
                    "utilidad_unitaria": p.get("utilidad_unitaria", 0.0),
                }
            )

        restricciones = []
        for r in recursos:
            rid = r.get("id")
            restricciones.append(
                {
                    "id": f"R_{rid}",
                    "recurso_id": rid,
                    "nombre": r.get("nombre", rid),
                    "coeficientes": dict(consumos.get(rid, {}) or {}),
                    "sentido": "<=",
                    "valor_derecho": r.get("disponibilidad"),
                    "unidad": r.get("unidad"),
                }
            )

        for i, extra in enumerate(restricciones_extra):
            e = copy.deepcopy(extra) if isinstance(extra, dict) else {}
            if not e.get("id"):
                e["id"] = e.get("restriccion_id") or f"EXTRA_{i+1}"
            coefs_e = dict(e.get("coeficientes", {}) or {})
            # completar coeficientes faltantes en 0 para variables de decision
            for p in productos:
                pid = p.get("id")
                coefs_e.setdefault(pid, 0.0)
            e["coeficientes"] = coefs_e
            e["sentido"] = _norm_sentido_rest(e.get("sentido", "<="))
            restricciones.append(e)

        objetivo_txt = str(problema.get("objetivo", "maximizar")).lower()
        return {
            "PROBLEMA": problema,
            "VARIABLES": variables,
            "FUNCION_OBJETIVO": {
                "sentido": "min" if objetivo_txt in {"min", "minimizar"} else "max",
                "coeficientes": {p.get("id"): p.get("utilidad_unitaria", 0.0) for p in productos},
            },
            "RESTRICCIONES": restricciones,
            "ESCENARIO_BASE": datos.get("ESCENARIO_BASE"),
            "RESTRICCIONES_ADICIONALES": restricciones_extra,
            "_origen": "compat",
        }

    return None


def _estado_solver(status_code: Any) -> Tuple[str, bool, bool, bool]:
    raw = status_code
    if hasattr(status_code, "status"):
        status_code = getattr(status_code, "status")

    miembros = getattr(pulp_constants, "LpStatus", {}) or {}
    opt_vals = {1, getattr(pulp_constants, "LpStatusOptimal", 1)}
    inf_vals = {-1, getattr(pulp_constants, "LpStatusInfeasible", -1)}
    unb_vals = {-2, getattr(pulp_constants, "LpStatusUnbounded", -2)}
    solve_status = getattr(pulp_constants, "LpSolveStatus", None)
    if solve_status is not None and hasattr(solve_status, "__members__"):
        for name, member in solve_status.__members__.items():
            val = getattr(member, "value", member)
            n = name.lower()
            if "optimal" in n:
                opt_vals.update({val, str(val), name})
            elif "infeasible" in n:
                inf_vals.update({val, str(val), name})
            elif "unbounded" in n:
                unb_vals.update({val, str(val), name})

    def _val_code(code: Any):
        return getattr(code, "value", code)

    sc = _val_code(status_code)
    sc_str = str(status_code)
    raw_str = str(raw)
    es_optimo = (sc in opt_vals) or (sc_str in {str(x) for x in opt_vals}) or ("Optimal" in sc_str) or ("Optimal" in raw_str)
    es_infactible = (sc in inf_vals) or (sc_str in {str(x) for x in inf_vals}) or ("Infeasible" in sc_str) or ("Infeasible" in raw_str)
    es_no_acotado = (sc in unb_vals) or (sc_str in {str(x) for x in unb_vals}) or ("Unbounded" in sc_str) or ("Unbounded" in raw_str)

    nombre = None
    if isinstance(miembros, dict):
        nombre = miembros.get(sc) or miembros.get(status_code)
    if not nombre and hasattr(status_code, "name"):
        nombre = str(status_code.name)
    if not nombre and solve_status is not None and hasattr(solve_status, "__members__"):
        for n, m in solve_status.__members__.items():
            if m == status_code or getattr(m, "value", m) == sc:
                nombre = n
                break
    if not nombre:
        nombre = sc_str
    mapa_nombre = {
        "1": "Optimal", "Optimal": "Optimal",
        "-1": "Infeasible", "Infeasible": "Infeasible",
        "-2": "Unbounded", "Unbounded": "Unbounded",
        "0": "Not Solved", "NotSolved": "Not Solved", "Not Solved": "Not Solved",
        "-3": "Undefined", "Undefined": "Undefined",
    }
    nombre = mapa_nombre.get(str(nombre), str(nombre))
    if es_optimo:
        nombre = "Optimal"
    elif es_infactible:
        nombre = "Infeasible"
    elif es_no_acotado:
        nombre = "Unbounded"
    return nombre, es_optimo, es_infactible, es_no_acotado


def _resolver_solver(modelo: pulp.LpProblem) -> Any:
    for factory in (lambda: pulp.HiGHS(msg=False), lambda: pulp.PULP_CBC_CMD(msg=False)):
        try:
            solver = factory()
        except Exception:
            solver = None
        if solver is None:
            continue
        try:
            return modelo.solve(solver)
        except Exception:
            continue
    return modelo.solve()


def resolver_modelo(datos: Dict[str, Any], entero: Optional[bool] = None) -> Dict[str, Any]:
    """Construye y resuelve el modelo y devuelve un resultado estructurado y serializable.

    Nota: `entero` se mantiene por retrocompatibilidad de firma pero se ignora; el tipo
    de cada variable se toma de su definicion individual.
    """
    _ = entero  # compatibilidad de firma, sin forzar tipos globales
    es_valido, errores = validar_datos_modelo(datos)
    snapshot = generar_snapshot_entrada(datos)
    inicio = time.perf_counter()
    timestamp = datetime.now(timezone.utc).isoformat()

    cfg = _normalizar_config(datos) if isinstance(datos, dict) else None
    problema_in = (datos.get("PROBLEMA", {}) if isinstance(datos, dict) else {}) or {}
    problema = copy.deepcopy((cfg or {}).get("PROBLEMA", problema_in))
    variables_cfg = list((cfg or {}).get("VARIABLES", []) or [])
    restricciones_cfg = list((cfg or {}).get("RESTRICCIONES", []) or [])
    fo_cfg = copy.deepcopy((cfg or {}).get("FUNCION_OBJETIVO", {}) or {})
    tipos_decision = [_norm_tipo_var(v.get("tipo")) for v in variables_cfg]
    clasificacion = clasificar_modelo(tipos_decision)
    problema["tipo_modelo"] = clasificacion
    problema["clasificacion_matematica"] = clasificacion

    base_respuesta = {
        "PROBLEMA": problema,
        "PRODUCTO": copy.deepcopy(datos.get("PRODUCTO", [])) if isinstance(datos, dict) else [],
        "RECURSO": copy.deepcopy(datos.get("RECURSO", [])) if isinstance(datos, dict) else [],
        "CONSUMO_RECURSO": copy.deepcopy(datos.get("CONSUMO_RECURSO", {})) if isinstance(datos, dict) else {},
        "VARIABLES": [copy.deepcopy(v) for v in variables_cfg],
        "RESTRICCIONES": [copy.deepcopy(r) for r in restricciones_cfg],
        "RESTRICCIONES_ADICIONALES": copy.deepcopy(datos.get("RESTRICCIONES_ADICIONALES", [])) if isinstance(datos, dict) else [],
        "FUNCION_OBJETIVO": fo_cfg,
        "RESULTADO_PRODUCTO": [],
        "RESULTADO_RECURSO": [],
        "RESULTADO_VARIABLES": [],
        "RESULTADO_RESTRICCIONES": [],
        "ANALISIS_IA": {},
        "utilidad_total": None,
        "valor_objetivo": None,
        "errores": list(errores),
    }

    if not es_valido or cfg is None:
        duracion = time.perf_counter() - inicio
        base_respuesta["EJECUCION"] = {
            "estado_proceso": "ERROR_VALIDACION",
            "estado_solver": None,
            "tiempo_ejecucion_seg": duracion,
            "timestamp_utc": timestamp,
            "tipo_modelo": clasificacion,
            "clasificacion_matematica": clasificacion,
            "snapshot_entrada": snapshot,
        }
        return base_respuesta

    sentido = _norm_sentido_obj(fo_cfg.get("sentido", problema.get("objetivo", "max")))
    sentido_pulp = pulp.LpMaximize if sentido == "max" else pulp.LpMinimize
    nombre_modelo = str(problema.get("id") or problema.get("nombre") or "Modelo_Optimizacion").replace(" ", "_")
    modelo = pulp.LpProblem(nombre_modelo, sentido_pulp)

    # Variables de decision
    x_vars: Dict[Any, pulp.LpVariable] = {}
    for v in variables_cfg:
        vid = v.get("id")
        tipo = _norm_tipo_var(v.get("tipo"))
        if tipo == "binary":
            cat = pulp.LpBinary
            lb_def, ub_def = 0, 1
        elif tipo == "integer":
            cat = pulp.LpInteger
            lb_def, ub_def = 0, None
        else:
            cat = pulp.LpContinuous
            lb_def, ub_def = 0, None
        lb = v.get("cota_inferior", lb_def)
        ub = v.get("cota_superior", ub_def)
        if tipo == "binary":
            lb = 0 if lb is None else float(lb)
            ub = 1 if ub is None else float(ub)
        else:
            lb = float(lb) if lb is not None else 0.0
            ub = float(ub) if ub is not None else None
        x_vars[vid] = modelo.add_variable(name=f"x_{vid}", lowBound=lb, upBound=ub, cat=cat)

    coef_obj = fo_cfg.get("coeficientes", {}) or {}
    modelo += pulp.lpSum(float(coef_obj.get(vid, 0.0) or 0.0) * x_vars[vid] for vid in x_vars), "Funcion_Objetivo"

    # Restricciones y holguras explicitas y_r para <=
    restricciones_info = []
    slack_vars: Dict[Any, pulp.LpVariable] = {}
    for i, r in enumerate(restricciones_cfg):
        rid = r.get("id") or r.get("recurso_id") or f"R{i+1}"
        sentido_r = _norm_sentido_rest(r.get("sentido", "<="))
        rhs = float(r.get("valor_derecho"))
        coefs = r.get("coeficientes", {}) or {}
        expr = pulp.lpSum(float(coefs.get(vid, 0.0) or 0.0) * x_vars[vid] for vid in x_vars)
        nombre_r = f"Restr_{rid}"
        if sentido_r == "<=":
            modelo += (expr <= rhs, nombre_r)
            y = modelo.add_variable(name=f"y_{rid}", lowBound=0)
            slack_vars[rid] = y
            modelo += (expr + y == rhs, f"Holgura_{rid}")
        elif sentido_r == ">=":
            modelo += (expr >= rhs, nombre_r)
        else:
            modelo += (expr == rhs, nombre_r)
        restricciones_info.append({"_rid": rid, "_nombre": nombre_r, "_sentido": sentido_r, "_rhs": rhs, "_coefs": coefs, **copy.deepcopy(r)})

    status_code = _resolver_solver(modelo)
    estado_solver, es_optimo, es_infactible, es_no_acotado = _estado_solver(status_code)
    duracion = time.perf_counter() - inicio

    ejecucion: Dict[str, Any] = {
        "estado_proceso": "NO_OPTIMO",
        "estado_solver": estado_solver,
        "tiempo_ejecucion_seg": duracion,
        "timestamp_utc": timestamp,
        "tipo_modelo": clasificacion,
        "clasificacion_matematica": clasificacion,
        "tipo_variables_decision": sorted(set(tipos_decision)),
        "snapshot_entrada": snapshot,
    }

    if not es_optimo:
        if es_infactible:
            ejecucion["estado_proceso"] = "INFACTIBLE"
        elif es_no_acotado:
            ejecucion["estado_proceso"] = "NO_ACOTADO"
        else:
            ejecucion["estado_proceso"] = "NO_OPTIMO"
        base_respuesta["EJECUCION"] = ejecucion
        return base_respuesta

    # Extraer y validar valores de decision
    valores_vars: Dict[Any, float] = {}
    for vid, var in x_vars.items():
        raw = pulp.value(var)
        try:
            val = float(raw)
        except Exception:
            ejecucion["estado_proceso"] = "ERROR_VALIDACION_RESULTADO"
            base_respuesta["errores"].append(f"Valor no numerico para variable {vid}.")
            base_respuesta["EJECUCION"] = ejecucion
            return base_respuesta
        if not math.isfinite(val):
            ejecucion["estado_proceso"] = "ERROR_VALIDACION_RESULTADO"
            base_respuesta["errores"].append(f"Valor no finito para variable {vid}.")
            base_respuesta["EJECUCION"] = ejecucion
            return base_respuesta
        tipo = _norm_tipo_var(next(v.get("tipo") for v in variables_cfg if v.get("id") == vid))
        if tipo in {"integer", "binary"}:
            red = round(val)
            if abs(val - red) > _INT_TOL:
                ejecucion["estado_proceso"] = "ERROR_VALIDACION_RESULTADO"
                base_respuesta["errores"].append(f"Variable {vid} esperada entera/binaria pero obtuvo {val}.")
                base_respuesta["EJECUCION"] = ejecucion
                return base_respuesta
            val = float(int(red))
            if tipo == "binary":
                val = 1.0 if val >= 0.5 else 0.0
        else:
            if abs(val) <= _TOL:
                val = 0.0
            val = float(round(val + 0.0, 12))
        valores_vars[vid] = val

    obj_raw = pulp.value(modelo.objective)
    try:
        valor_obj = float(obj_raw)
    except Exception:
        ejecucion["estado_proceso"] = "ERROR_VALIDACION_RESULTADO"
        base_respuesta["errores"].append("Valor objetivo no numerico.")
        base_respuesta["EJECUCION"] = ejecucion
        return base_respuesta
    if not math.isfinite(valor_obj):
        ejecucion["estado_proceso"] = "ERROR_VALIDACION_RESULTADO"
        base_respuesta["errores"].append("Valor objetivo no finito.")
        base_respuesta["EJECUCION"] = ejecucion
        return base_respuesta
    if abs(valor_obj) <= _TOL:
        valor_obj = 0.0
    valor_obj = float(round(valor_obj + 0.0, 12))

    resultado_vars = []
    for v in variables_cfg:
        vid = v.get("id")
        val = valores_vars.get(vid, 0.0)
        cobj = float(coef_obj.get(vid, 0.0) or 0.0)
        contrib = float(round(cobj * val + 0.0, 12))
        resultado_vars.append(
            {
                "variable_id": vid,
                "nombre": v.get("nombre", vid),
                "tipo": _norm_tipo_var(v.get("tipo")),
                "valor": val,
                "coeficiente_objetivo": cobj,
                "contribucion_objetivo": contrib,
            }
        )

    resultado_restr = []
    for info in restricciones_info:
        rid = info.get("_rid")
        sentido_r = info.get("_sentido")
        rhs = float(info.get("_rhs"))
        coefs = info.get("_coefs") or {}
        lhs = 0.0
        for vid, val in valores_vars.items():
            lhs += float(coefs.get(vid, 0.0) or 0.0) * float(val)
        lhs = float(round(lhs + 0.0, 12))
        if sentido_r == "<=":
            holgura = rhs - lhs
        elif sentido_r == ">=":
            holgura = lhs - rhs
        else:
            holgura = 0.0
        if abs(holgura) <= _TOL:
            holgura = 0.0
        holgura = float(round(holgura + 0.0, 12))
        if holgura < -1e-6:
            ejecucion["estado_proceso"] = "ERROR_VALIDACION_RESULTADO"
            base_respuesta["errores"].append(f"Holgura negativa significativa en restriccion {rid}.")
            base_respuesta["EJECUCION"] = ejecucion
            return base_respuesta
        if holgura < 0:
            holgura = 0.0
        y_val = None
        if rid in slack_vars:
            try:
                y_val = float(pulp.value(slack_vars[rid]))
            except Exception:
                y_val = holgura
            if y_val is not None and abs(y_val) <= _TOL:
                y_val = 0.0
            if y_val is not None:
                y_val = float(round(y_val + 0.0, 12))
        estado_rec = _estado_holgura(holgura) if sentido_r in {"<=", ">="} else "ACTIVA"
        item = {
            "restriccion_id": rid,
            "recurso_id": info.get("recurso_id", rid),
            "nombre": info.get("nombre", rid),
            "sentido": sentido_r,
            "valor_derecho": rhs,
            "lado_izquierdo": lhs,
            "consumo_total": lhs if sentido_r == "<=" else None,
            "holgura": holgura,
            "variable_holgura": f"y_{rid}" if sentido_r == "<=" else None,
            "valor_variable_holgura": y_val,
            "estado_recurso": estado_rec,
        }
        if info.get("unidad") is not None:
            item["unidad"] = info.get("unidad")
        resultado_restr.append(item)

    # Compatibilidad producto/recurso para formato compat
    resultado_producto = []
    resultado_recurso = []
    if cfg.get("_origen") == "compat":
        for rv in resultado_vars:
            resultado_producto.append(
                {
                    "producto_id": rv["variable_id"],
                    "nombre": rv.get("nombre", rv["variable_id"]),
                    "cantidad_producir": rv["valor"],
                    "utilidad_unitaria": float(coef_obj.get(rv["variable_id"], 0.0) or 0.0),
                    "utilidad_total_producto": rv["contribucion_objetivo"],
                }
            )
        for rr in resultado_restr:
            if rr.get("recurso_id") is not None or str(rr.get("restriccion_id", "")).startswith("R_"):
                resultado_recurso.append(
                    {
                        "recurso_id": rr.get("recurso_id", rr.get("restriccion_id")),
                        "nombre": rr.get("nombre", rr.get("restriccion_id")),
                        "disponibilidad": rr["valor_derecho"],
                        "consumo_total": rr.get("lado_izquierdo"),
                        "holgura": rr.get("holgura"),
                        "variable_holgura": rr.get("variable_holgura"),
                        "valor_variable_holgura": rr.get("valor_variable_holgura"),
                        "estado_recurso": rr.get("estado_recurso"),
                        **({"unidad": rr["unidad"]} if "unidad" in rr else {}),
                    }
                )

    ejecucion["estado_proceso"] = "OPTIMO"
    base_respuesta.update(
        {
            "EJECUCION": ejecucion,
            "RESULTADO_VARIABLES": resultado_vars,
            "RESULTADO_RESTRICCIONES": resultado_restr,
            "RESULTADO_PRODUCTO": resultado_producto if cfg.get("_origen") == "compat" else base_respuesta["RESULTADO_PRODUCTO"],
            "RESULTADO_RECURSO": resultado_recurso if cfg.get("_origen") == "compat" else base_respuesta["RESULTADO_RECURSO"],
            "valor_objetivo": valor_obj,
            "utilidad_total": valor_obj,
            "errores": [],
        }
    )
    return base_respuesta
