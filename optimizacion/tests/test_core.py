"""Pruebas del modulo de optimizacion (motor, validaciones y analytics)."""

from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from optimizacion.analytics.comparador import comparar_escenarios
from optimizacion.analytics.sensibilidad import analizar_sensibilidad_recursos
from optimizacion.core.datos_ejercicio6 import obtener_datos_ejercicio6
from optimizacion.core.motor_pulp import resolver_modelo
from optimizacion.core.validaciones import validar_datos_modelo


def _produccion_map(resultado):
    return {r["producto_id"]: r["cantidad_producir"] for r in resultado.get("RESULTADO_PRODUCTO", [])}


def _recursos_map(resultado):
    return {r["recurso_id"]: r for r in resultado.get("RESULTADO_RECURSO", [])}


def _var_map(resultado):
    return {r["variable_id"]: r["valor"] for r in resultado.get("RESULTADO_VARIABLES", [])}


# =========================
# Ejercicio 6 (caso referencia) - verificaciones intactas
# =========================

def test_solucion_optima_ejercicio6_valores_exactos():
    datos = obtener_datos_ejercicio6()
    resultado = resolver_modelo(datos)
    ejec = resultado["EJECUCION"]

    assert ejec["estado_proceso"] == "OPTIMO"
    assert ejec["estado_solver"] == "Optimal"
    assert ejec.get("clasificacion_matematica") == "PLE/IP"
    assert abs(resultado["utilidad_total"] - 64800.0) <= 1e-6

    prod = _produccion_map(resultado)
    assert prod == {"P1": 273.0, "P2": 390.0, "P3": 0.0, "P4": 1.0, "P5": 0.0}

    rec = _recursos_map(resultado)
    assert abs(rec["MPA"]["consumo_total"] - 2264.0) <= 1e-6
    assert abs(rec["MPB"]["consumo_total"] - 2500.0) <= 1e-6
    assert abs(rec["HM"]["consumo_total"] - 1600.0) <= 1e-6
    assert abs(rec["MPA"]["holgura"] - 736.0) <= 1e-6
    assert abs(rec["MPB"]["holgura"] - 0.0) <= 1e-6
    assert abs(rec["HM"]["holgura"] - 0.0) <= 1e-6


def test_consistencia_ecuaciones_y_holguras_ejercicio6():
    datos = obtener_datos_ejercicio6()
    resultado = resolver_modelo(datos)
    assert resultado["EJECUCION"]["estado_proceso"] == "OPTIMO"

    prod = _produccion_map(resultado)
    rec = _recursos_map(resultado)
    tol = 1e-6

    for p in datos["PRODUCTO"]:
        assert prod[p["id"]] >= -tol
        assert abs(prod[p["id"]] - round(prod[p["id"]])) <= tol

    utilidad_calc = sum(p["utilidad_unitaria"] * prod[p["id"]] for p in datos["PRODUCTO"])
    assert abs(utilidad_calc - resultado["utilidad_total"]) <= 1e-6

    for r in datos["RECURSO"]:
        rid = r["id"]
        consumo = sum(datos["CONSUMO_RECURSO"][rid][p["id"]] * prod[p["id"]] for p in datos["PRODUCTO"])
        holgura = rec[rid]["holgura"]
        assert abs(consumo - rec[rid]["consumo_total"]) <= tol
        assert abs((consumo + holgura) - r["disponibilidad"]) <= tol
        assert holgura >= -tol
        if abs(holgura) <= tol:
            assert rec[rid]["estado_recurso"] in {"AGOTADO", "ACTIVA"}
        else:
            assert rec[rid]["estado_recurso"] == "CON_HOLGURA"


def test_escenario_base_infactible_sin_porcentaje_mejora_ej6():
    datos = obtener_datos_ejercicio6()
    resultado = resolver_modelo(datos)
    comp = comparar_escenarios(datos, resultado)

    base = comp["escenario_base"]
    assert base["es_factible"] is False
    assert base["infactibilidad_demostrada"] is True
    assert abs(base["utilidad_reportada_enunciado"] - 64500.0) <= 1e-6
    assert abs(base["utilidad_calculada"] - 70500.0) <= 1e-6
    assert len(base["motivos_no_factibilidad"]) >= 1

    c = comp["comparacion"]
    assert c["comparacion_valida"] is False
    assert c["incremento_absoluto"] is None
    assert c["incremento_porcentual"] is None


# =========================
# Nuevos modelos: 3x4 continuo (PL/LP) y 8x5 mixto (MILP)
# =========================

def _modelo_3x4_continuo():
    # Optimo esperado: P1=0, P2=20, P3=60, Z=3600
    return {
        "PROBLEMA": {"id": "M3X4", "nombre": "3x4 continuo", "objetivo": "maximizar"},
        "PRODUCTO": [
            {"id": "P1", "nombre": "P1", "utilidad_unitaria": 40.0, "tipo_variable": "Continuous"},
            {"id": "P2", "nombre": "P2", "utilidad_unitaria": 30.0, "tipo_variable": "Continuous"},
            {"id": "P3", "nombre": "P3", "utilidad_unitaria": 50.0, "tipo_variable": "Continuous"},
        ],
        "RECURSO": [
            {"id": "R1", "nombre": "R1", "disponibilidad": 100.0},
            {"id": "R2", "nombre": "R2", "disponibilidad": 80.0},
            {"id": "R3", "nombre": "R3", "disponibilidad": 120.0},
            {"id": "R4", "nombre": "R4", "disponibilidad": 60.0},
        ],
        "CONSUMO_RECURSO": {
            "R1": {"P1": 2, "P2": 1, "P3": 1},
            "R2": {"P1": 1, "P2": 2, "P3": 1},
            "R3": {"P1": 1, "P2": 1, "P3": 2},
            "R4": {"P1": 1, "P2": 0.5, "P3": 1},
        },
        "RESTRICCIONES_ADICIONALES": [],
        "ESCENARIO_BASE": {
            "descripcion": "Base factible",
            "produccion": {"P1": 0, "P2": 0, "P3": 0},
            "utilidad_reportada_enunciado": 0,
        },
    }


def test_modelo_3x4_continuo_pl_lp():
    datos = _modelo_3x4_continuo()
    res = resolver_modelo(datos)
    assert res["EJECUCION"]["estado_proceso"] == "OPTIMO"
    assert res["EJECUCION"]["clasificacion_matematica"] == "PL/LP"
    vals = _var_map(res)
    assert abs(vals["P1"] - 0.0) <= 1e-6
    assert abs(vals["P2"] - (40.0 / 3.0)) <= 1e-6
    assert abs(vals["P3"] - (160.0 / 3.0)) <= 1e-6
    assert abs(res["valor_objetivo"] - (9200.0 / 3.0)) <= 1e-6
    # variables continuas: verificar precision decimal controlada (no redondeo entero)
    tipos = {v["variable_id"]: v["tipo"] for v in res["RESULTADO_VARIABLES"]}
    assert all(t == "continuous" for t in tipos.values())


def _modelo_8x5_mixto():
    return {
        "PROBLEMA": {"id": "M8X5", "nombre": "8x5 mixto", "objetivo": "maximizar"},
        "PRODUCTO": [
            {"id": "P1", "nombre": "P1", "utilidad_unitaria": 20, "tipo_variable": "Integer"},
            {"id": "P2", "nombre": "P2", "utilidad_unitaria": 15, "tipo_variable": "Integer"},
            {"id": "P3", "nombre": "P3", "utilidad_unitaria": 25, "tipo_variable": "Continuous"},
            {"id": "P4", "nombre": "P4", "utilidad_unitaria": 10, "tipo_variable": "Continuous"},
            {"id": "P5", "nombre": "P5", "utilidad_unitaria": 30, "tipo_variable": "Integer"},
            {"id": "P6", "nombre": "P6", "utilidad_unitaria": 12, "tipo_variable": "Continuous"},
            {"id": "P7", "nombre": "P7", "utilidad_unitaria": 18, "tipo_variable": "Binary"},
            {"id": "P8", "nombre": "P8", "utilidad_unitaria": 22, "tipo_variable": "Binary"},
        ],
        "RECURSO": [
            {"id": "R1", "nombre": "R1", "disponibilidad": 100},
            {"id": "R2", "nombre": "R2", "disponibilidad": 80},
            {"id": "R3", "nombre": "R3", "disponibilidad": 120},
            {"id": "R4", "nombre": "R4", "disponibilidad": 90},
            {"id": "R5", "nombre": "R5", "disponibilidad": 70},
        ],
        "CONSUMO_RECURSO": {
            "R1": {"P1": 2, "P2": 1, "P3": 3, "P4": 1, "P5": 2, "P6": 1, "P7": 5, "P8": 4},
            "R2": {"P1": 1, "P2": 2, "P3": 1, "P4": 2, "P5": 1, "P6": 1, "P7": 3, "P8": 2},
            "R3": {"P1": 2, "P2": 2, "P3": 1, "P4": 1, "P5": 3, "P6": 2, "P7": 2, "P8": 5},
            "R4": {"P1": 1, "P2": 1, "P3": 2, "P4": 1, "P5": 1, "P6": 2, "P7": 4, "P8": 1},
            "R5": {"P1": 1, "P2": 0, "P3": 1, "P4": 2, "P5": 2, "P6": 1, "P7": 1, "P8": 3},
        },
        "RESTRICCIONES_ADICIONALES": [],
    }


def test_modelo_8x5_mixto_milp():
    datos = _modelo_8x5_mixto()
    res = resolver_modelo(datos)
    assert res["EJECUCION"]["estado_proceso"] == "OPTIMO"
    assert res["EJECUCION"]["clasificacion_matematica"] == "MILP"
    tipos = {v["variable_id"]: v["tipo"] for v in res["RESULTADO_VARIABLES"]}
    assert "integer" in tipos.values()
    assert "continuous" in tipos.values()
    assert "binary" in tipos.values()
    # binarios en {0,1}, enteros sin fraccion
    vals = _var_map(res)
    for vid in ["P7", "P8"]:
        assert vals[vid] in (0.0, 1.0)
    for vid in ["P1", "P2", "P5"]:
        assert abs(vals[vid] - round(vals[vid])) <= 1e-9


# =========================
# Restricciones adicionales (min/max, <=, >=, ==)
# =========================

def test_restricciones_adicionales_min_max_y_operadores():
    datos = _modelo_3x4_continuo()
    datos["RESTRICCIONES_ADICIONALES"] = [
        {"id": "MIN_P2", "nombre": "Minimo P2", "coeficientes": {"P2": 1}, "sentido": ">=", "valor_derecho": 25},
        {"id": "MAX_P3", "nombre": "Maximo P3", "coeficientes": {"P3": 1}, "sentido": "<=", "valor_derecho": 40},
        {"id": "EQ_P1", "nombre": "Fijar P1", "coeficientes": {"P1": 1}, "sentido": "==", "valor_derecho": 5},
    ]
    ok, errores = validar_datos_modelo(datos)
    assert ok, errores
    res = resolver_modelo(datos)
    assert res["EJECUCION"]["estado_proceso"] == "OPTIMO"
    vals = _var_map(res)
    assert vals["P2"] >= 25 - 1e-6
    assert vals["P3"] <= 40 + 1e-6
    assert abs(vals["P1"] - 5.0) <= 1e-6


def test_limites_min_max_produccion_por_producto():
    datos = _modelo_3x4_continuo()
    # aplicar min/max en definicion de producto
    for p in datos["PRODUCTO"]:
        if p["id"] == "P2":
            p["limite_inferior"] = 30
        if p["id"] == "P3":
            p["limite_superior"] = 30
    res = resolver_modelo(datos)
    assert res["EJECUCION"]["estado_proceso"] == "OPTIMO"
    vals = _var_map(res)
    assert vals["P2"] >= 30 - 1e-6
    assert vals["P3"] <= 30 + 1e-6


# =========================
# Modificacion dinamica de utilidades y coeficientes
# =========================

def test_modificacion_dinamica_utilidades_y_coeficientes():
    datos = _modelo_3x4_continuo()
    base = resolver_modelo(datos)
    z_base = base["valor_objetivo"]
    vals_base = _var_map(base)

    datos_mod = copy.deepcopy(datos)
    # aumentar utilidad de P1 significativamente
    for p in datos_mod["PRODUCTO"]:
        if p["id"] == "P1":
            p["utilidad_unitaria"] = 200.0
    res_mod = resolver_modelo(datos_mod)
    assert res_mod["EJECUCION"]["estado_proceso"] == "OPTIMO"
    vals_mod = _var_map(res_mod)
    assert vals_mod["P1"] > 0.0
    assert res_mod["valor_objetivo"] > z_base

    # modificar coeficiente de consumo para restringir mas
    datos_mod2 = copy.deepcopy(datos)
    datos_mod2["CONSUMO_RECURSO"]["R1"]["P3"] = 10  # mucho mas caro en recurso critico
    res_mod2 = resolver_modelo(datos_mod2)
    assert res_mod2["EJECUCION"]["estado_proceso"] == "OPTIMO"
    vals_mod2 = _var_map(res_mod2)
    assert vals_mod2["P3"] < vals_base["P3"]  # menor que en optimo original


# =========================
# Comparador y sensibilidad sobre nuevos modelos
# =========================

def test_comparador_sobre_modelo_nuevo():
    datos = _modelo_3x4_continuo()
    # escenario base factible
    datos["ESCENARIO_BASE"] = {
        "descripcion": "Base",
        "produccion": {"P1": 10, "P2": 10, "P3": 10},
        "utilidad_reportada_enunciado": 1200.0,
    }
    res = resolver_modelo(datos)
    comp = comparar_escenarios(datos, res)
    assert comp["escenario_base"]["es_factible"] is True
    assert comp["comparacion"]["comparacion_valida"] is True
    assert comp["comparacion"]["incremento_absoluto"] is not None
    assert abs(comp["escenario_optimo"]["utilidad_total"] - (9200.0 / 3.0)) <= 1e-6


def test_sensibilidad_sobre_modelo_nuevo():
    datos = _modelo_3x4_continuo()
    sens = analizar_sensibilidad_recursos(datos, variacion_porcentaje=10.0)
    assert sens["metodo"] == "analisis_escenarios_disponibilidad"
    assert "escenarios" in sens.get("tipo_resultado", "") or sens.get("tipo_resultado") == "escenarios"
    assert "sensibilidad por escenarios" in sens["interpretacion"].lower() or "analisis de sensibilidad" in sens["interpretacion"].lower()
    assert "precios sombra" in sens["interpretacion"].lower() or "duales" in sens["interpretacion"].lower()
    assert sens.get("limitaciones")
    assert len(sens["resultados_por_recurso"]) == 4
    for r in sens["resultados_por_recurso"]:
        esc = r.get("escenarios", {})
        assert "menos" in esc or "menos_10" in esc
        assert "mas" in esc or "mas_10" in esc
        for e in esc.values():
            assert "delta_utilidad" in e
            assert "produccion" in e  # impacto en x_p
    assert sens.get("recurso_mayor_impacto") is not None


# =========================
# Entradas invalidas y deteccion de no acotados / infactibles
# =========================

def test_rechazo_entradas_invalidas():
    datos = obtener_datos_ejercicio6()
    # NaN
    datos_nan = copy.deepcopy(datos)
    datos_nan["RECURSO"][0]["disponibilidad"] = float("nan")
    ok, errores = validar_datos_modelo(datos_nan)
    assert not ok and errores
    res = resolver_modelo(datos_nan)
    assert res["EJECUCION"]["estado_proceso"] == "ERROR_VALIDACION"

    # Cotas invertidas
    datos_cotas = copy.deepcopy(_modelo_3x4_continuo())
    datos_cotas["PRODUCTO"][0]["limite_inferior"] = 10
    datos_cotas["PRODUCTO"][0]["limite_superior"] = 5
    ok, errores = validar_datos_modelo(datos_cotas)
    assert not ok and any("cota" in e.lower() for e in errores)

    # Referencias inexistentes en consumos
    datos_ref = copy.deepcopy(datos)
    datos_ref["CONSUMO_RECURSO"]["MPA"]["PX"] = 1.0
    ok, errores = validar_datos_modelo(datos_ref)
    assert not ok and any("inexistente" in e.lower() for e in errores)

    # Duplicados
    datos_dup = copy.deepcopy(datos)
    datos_dup["PRODUCTO"].append(copy.deepcopy(datos_dup["PRODUCTO"][0]))
    ok, errores = validar_datos_modelo(datos_dup)
    assert not ok and any("duplic" in e.lower() for e in errores)

    # Infinito
    datos_inf = copy.deepcopy(datos)
    datos_inf["PRODUCTO"][0]["utilidad_unitaria"] = float("inf")
    ok, errores = validar_datos_modelo(datos_inf)
    assert not ok


def test_modelo_no_acotado_detectado():
    cfg = {
        "PROBLEMA": {"id": "UNB", "nombre": "No acotado", "objetivo": "maximizar"},
        "PRODUCTO": [
            {"id": "X1", "nombre": "X1", "utilidad_unitaria": 5.0, "tipo_variable": "Continuous"}
        ],
        "RECURSO": [],
        "CONSUMO_RECURSO": {},
        "RESTRICCIONES_ADICIONALES": [],
    }
    ok, errores = validar_datos_modelo(cfg)
    assert not ok
    assert any("no acotado" in e.lower() for e in errores)
    res = resolver_modelo(cfg)
    assert res["EJECUCION"]["estado_proceso"] == "ERROR_VALIDACION"


def test_modelo_infactible_detectado():
    cfg = {
        "PROBLEMA": {"id": "INF", "nombre": "Infactible", "objetivo": "maximizar"},
        "PRODUCTO": [
            {"id": "X1", "nombre": "X1", "utilidad_unitaria": 1.0, "tipo_variable": "Continuous"}
        ],
        "RECURSO": [],
        "CONSUMO_RECURSO": {},
        "RESTRICCIONES_ADICIONALES": [
            {"id": "C1", "nombre": "C1", "coeficientes": {"X1": 1}, "sentido": "<=", "valor_derecho": 5},
            {"id": "C2", "nombre": "C2", "coeficientes": {"X1": 1}, "sentido": ">=", "valor_derecho": 10},
        ],
    }
    ok, errores = validar_datos_modelo(cfg)
    assert ok, errores
    res = resolver_modelo(cfg)
    assert res["EJECUCION"]["estado_proceso"] == "INFACTIBLE"
    assert res.get("RESULTADO_VARIABLES", []) == []


def test_respetar_tipo_variable_individual_sin_forzar_global():
    # Mezcla explicita: aunque se pase entero=False/True legacy, debe respetar tipos individuales
    datos = _modelo_8x5_mixto()
    res1 = resolver_modelo(datos, entero=True)  # parametro legacy ignorado
    res2 = resolver_modelo(datos, entero=False)
    tipos1 = {v["variable_id"]: v["tipo"] for v in res1["RESULTADO_VARIABLES"]}
    tipos2 = {v["variable_id"]: v["tipo"] for v in res2["RESULTADO_VARIABLES"]}
    assert tipos1 == tipos2
    assert tipos1["P3"] == "continuous"
    assert tipos1["P1"] == "integer"
    assert tipos1["P7"] == "binary"
