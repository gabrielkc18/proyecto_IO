"""Generacion de reportes en consola, CSV, JSON y graficos PNG (dinamico n/m)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def asegurar_directorio_salida(base_dir: Path) -> Path:
    salida = base_dir / "outputs"
    salida.mkdir(parents=True, exist_ok=True)
    return salida


def _productos_resultado(resultado: Dict[str, Any]) -> List[Dict[str, Any]]:
    if resultado.get("RESULTADO_PRODUCTO"):
        return list(resultado.get("RESULTADO_PRODUCTO", []))
    filas = []
    for v in resultado.get("RESULTADO_VARIABLES", []) or []:
        filas.append(
            {
                "producto_id": v.get("variable_id"),
                "nombre": v.get("nombre", v.get("variable_id")),
                "cantidad_producir": v.get("valor"),
                "utilidad_unitaria": v.get("coeficiente_objetivo"),
                "utilidad_total_producto": v.get("contribucion_objetivo"),
            }
        )
    return filas


def _recursos_resultado(resultado: Dict[str, Any]) -> List[Dict[str, Any]]:
    if resultado.get("RESULTADO_RECURSO"):
        return list(resultado.get("RESULTADO_RECURSO", []))
    filas = []
    for r in resultado.get("RESULTADO_RESTRICCIONES", []) or []:
        filas.append(
            {
                "recurso_id": r.get("recurso_id", r.get("restriccion_id")),
                "nombre": r.get("nombre", r.get("restriccion_id")),
                "disponibilidad": r.get("valor_derecho"),
                "consumo_total": r.get("consumo_total", r.get("lado_izquierdo")),
                "holgura": r.get("holgura"),
                "estado_recurso": r.get("estado_recurso"),
                "unidad": r.get("unidad"),
            }
        )
    return filas


def _figsize(n_items: int, base_w: float = 10.0, base_h: float = 5.0, per_item: float = 0.45) -> tuple[float, float]:
    w = max(base_w, 4.0 + n_items * per_item)
    h = max(base_h, 4.0)
    return (min(w, 24.0), h)


def imprimir_tablas_consola(
    resultado_optimo: Dict[str, Any],
    comparacion: Dict[str, Any],
    sensibilidad: Dict[str, Any],
) -> None:
    ejec = resultado_optimo.get("EJECUCION", {}) or {}
    print(f"\n=== ESTADO EJECUCION: {ejec.get('estado_proceso')} / {ejec.get('estado_solver')} ===")
    clasif = ejec.get("clasificacion_matematica") or ejec.get("tipo_modelo")
    if clasif:
        print(f"Clasificacion matematica: {clasif}")

    print("\n=== RESULTADO OPTIMO POR PRODUCTO/VARIABLE ===")
    df_prod = pd.DataFrame(_productos_resultado(resultado_optimo))
    print(df_prod.to_string(index=False) if not df_prod.empty else "Sin resultados de producto/variable.")

    print("\n=== RESULTADO OPTIMO POR RECURSO/RESTRICCION ===")
    df_rec = pd.DataFrame(_recursos_resultado(resultado_optimo))
    print(df_rec.to_string(index=False) if not df_rec.empty else "Sin resultados de recurso/restriccion.")

    print("\n=== COMPARACION ESCENARIO BASE vs OPTIMO ===")
    base = comparacion.get("escenario_base", {})
    comp = comparacion.get("comparacion", {})
    print(f"Escenario base factible: {base.get('es_factible')}")
    print(f"Infactibilidad demostrada: {base.get('infactibilidad_demostrada')}")
    motivos = base.get("motivos_no_factibilidad") or []
    if motivos:
        for m in motivos:
            print(f"  - Motivo: {m}")
    print(f"Utilidad reportada enunciado: {base.get('utilidad_reportada_enunciado')}")
    print(f"Utilidad calculada base: {base.get('utilidad_calculada')}")
    print(f"Utilidad optima: {comparacion.get('escenario_optimo', {}).get('utilidad_total')}")
    if comp.get("comparacion_valida"):
        print(f"Incremento absoluto ({comp.get('referencia_incremento')}): {comp.get('incremento_absoluto')}")
        print(f"Incremento porcentual: {comp.get('incremento_porcentual')}")
    else:
        print(f"Comparacion de mejora no valida: {comp.get('motivo_no_comparacion')}")

    print("\n=== SENSIBILIDAD (ANALISIS POR ESCENARIOS) ===")
    print(sensibilidad.get("interpretacion", ""))
    if sensibilidad.get("limitaciones"):
        print(f"Limitaciones: {sensibilidad.get('limitaciones')}")
    filas: List[Dict[str, Any]] = []
    for r in sensibilidad.get("resultados_por_recurso", []):
        esc = r.get("escenarios", {}) or {}
        menos = esc.get("menos") or esc.get("menos_10") or {}
        mas = esc.get("mas") or esc.get("mas_10") or {}
        filas.append(
            {
                "recurso": r.get("recurso_nombre"),
                "utilidad_menos": menos.get("utilidad_total"),
                "utilidad_base": sensibilidad.get("utilidad_base"),
                "utilidad_mas": mas.get("utilidad_total"),
                "delta_menos": menos.get("delta_utilidad"),
                "delta_mas": mas.get("delta_utilidad"),
                "impacto_promedio_abs": r.get("impacto_promedio_abs"),
            }
        )
    df_sens = pd.DataFrame(filas)
    print(df_sens.to_string(index=False) if not df_sens.empty else "Sin resultados de sensibilidad.")
    mayor = sensibilidad.get("recurso_mayor_impacto")
    if mayor:
        print(f"Recurso/restriccion con mayor impacto (escenarios): {mayor.get('recurso_nombre')} ({mayor.get('impacto_promedio_abs')})")


def exportar_resultados_csv(resultado_optimo: Dict[str, Any], salida_dir: Path) -> List[Path]:
    rutas: List[Path] = []
    df_prod = pd.DataFrame(_productos_resultado(resultado_optimo))
    df_rec = pd.DataFrame(_recursos_resultado(resultado_optimo))

    ruta_prod = salida_dir / "resultados_productos.csv"
    ruta_rec = salida_dir / "resultados_recursos.csv"
    df_prod.to_csv(ruta_prod, index=False, encoding="utf-8-sig")
    df_rec.to_csv(ruta_rec, index=False, encoding="utf-8-sig")
    rutas.extend([ruta_prod, ruta_rec])

    if not df_prod.empty:
        df_prod_c = df_prod.add_prefix("producto_")
    else:
        df_prod_c = pd.DataFrame()
    if not df_rec.empty:
        df_rec_c = df_rec.add_prefix("recurso_")
    else:
        df_rec_c = pd.DataFrame()
    df_comb = pd.concat([df_prod_c, df_rec_c], ignore_index=True, sort=False)
    ruta_comb = salida_dir / "resultados_optimos.csv"
    df_comb.to_csv(ruta_comb, index=False, encoding="utf-8-sig")
    rutas.append(ruta_comb)
    return rutas


def exportar_contexto_ia(
    datos: Dict[str, Any],
    resultado_optimo: Dict[str, Any],
    comparacion: Dict[str, Any],
    sensibilidad: Dict[str, Any],
    salida_dir: Path,
) -> Path:
    contexto = {
        "PROBLEMA": datos.get("PROBLEMA", {}),
        "EJECUCION": resultado_optimo.get("EJECUCION", {}),
        "FUNCION_OBJETIVO": resultado_optimo.get("FUNCION_OBJETIVO", datos.get("FUNCION_OBJETIVO", {})),
        "VARIABLES": resultado_optimo.get("VARIABLES", datos.get("VARIABLES", [])),
        "RESTRICCIONES": resultado_optimo.get("RESTRICCIONES", datos.get("RESTRICCIONES", [])),
        "RESTRICCIONES_ADICIONALES": datos.get("RESTRICCIONES_ADICIONALES", []),
        "RESULTADO_PRODUCTO": _productos_resultado(resultado_optimo),
        "RESULTADO_RECURSO": _recursos_resultado(resultado_optimo),
        "RESULTADO_VARIABLES": resultado_optimo.get("RESULTADO_VARIABLES", []),
        "RESULTADO_RESTRICCIONES": resultado_optimo.get("RESULTADO_RESTRICCIONES", []),
        "COMPARACION": comparacion,
        "SENSIBILIDAD": sensibilidad,
    }
    ruta = salida_dir / "contexto_ia.json"
    with ruta.open("w", encoding="utf-8") as f:
        json.dump(contexto, f, ensure_ascii=False, indent=2)
    return ruta


def generar_graficos(
    resultado_optimo: Dict[str, Any], comparacion: Dict[str, Any], salida_dir: Path
) -> List[Path]:
    rutas: List[Path] = []
    productos = _productos_resultado(resultado_optimo)
    recursos = _recursos_resultado(resultado_optimo)

    # Grafico 1: objetivo/base y produccion
    n_prod = max(len(productos), 1)
    fig, axes = plt.subplots(1, 2, figsize=_figsize(n_prod, base_w=12.0, base_h=5.0))
    base = comparacion.get("escenario_base", {}) or {}
    comp = comparacion.get("comparacion", {}) or {}
    utilidad_opt = comparacion.get("escenario_optimo", {}).get("utilidad_total")
    if utilidad_opt is None:
        utilidad_opt = resultado_optimo.get("valor_objetivo", resultado_optimo.get("utilidad_total")) or 0
    if base.get("es_factible") and comp.get("comparacion_valida"):
        etiquetas_bar = ["Base (calculada)", "Optimo"]
        valores_bar = [base.get("utilidad_calculada", 0) or 0, utilidad_opt]
        colores = ["#0275d8", "#5cb85c"]
    elif base:
        etiquetas_bar = ["Base enunciado", "Optimo"]
        valores_bar = [base.get("utilidad_reportada_enunciado", 0) or 0, utilidad_opt]
        colores = ["#d9534f", "#5cb85c"]
    else:
        etiquetas_bar = ["Optimo"]
        valores_bar = [utilidad_opt]
        colores = ["#5cb85c"]
    axes[0].bar(etiquetas_bar, valores_bar, color=colores)
    axes[0].set_title("Valor objetivo / utilidad")
    axes[0].set_ylabel("Valor")
    axes[0].tick_params(axis="x", rotation=10)

    nombres = [str(p.get("producto_id", p.get("nombre", ""))) for p in productos]
    cantidades = [p.get("cantidad_producir", 0) or 0 for p in productos]
    axes[1].bar(nombres, cantidades, color="#0275d8")
    axes[1].set_title("Produccion optima por producto/variable")
    axes[1].set_ylabel("Cantidad")
    if len(nombres) > 6:
        axes[1].tick_params(axis="x", rotation=45)
    fig.tight_layout()
    ruta1 = salida_dir / "grafico_utilidad_y_produccion.png"
    fig.savefig(ruta1, dpi=150)
    plt.close(fig)
    rutas.append(ruta1)

    # Grafico 2: Consumo vs Disponibilidad y Holguras
    etiquetas = [str(r.get("recurso_id", r.get("nombre", ""))) for r in recursos]
    consumo = [r.get("consumo_total", 0) or 0 for r in recursos]
    disponibilidad = [r.get("disponibilidad", 0) or 0 for r in recursos]
    holgura = [r.get("holgura", 0) or 0 for r in recursos]
    estados = [str(r.get("estado_recurso", "")) for r in recursos]
    n_res = max(len(etiquetas), 1)

    fig2, axes2 = plt.subplots(1, 2, figsize=_figsize(n_res, base_w=13.0, base_h=5.0))
    x = list(range(len(etiquetas)))
    ancho = 0.35
    axes2[0].bar([i - ancho / 2 for i in x], consumo, width=ancho, label="Consumo", color="#f0ad4e")
    axes2[0].bar([i + ancho / 2 for i in x], disponibilidad, width=ancho, label="Disponibilidad", color="#5bc0de")
    axes2[0].set_xticks(x)
    axes2[0].set_xticklabels(etiquetas)
    axes2[0].set_title("Consumo vs Disponibilidad")
    axes2[0].legend()
    if len(etiquetas) > 6:
        axes2[0].tick_params(axis="x", rotation=45)
    unidades = [r.get("unidad") for r in recursos if r.get("unidad")]
    if unidades:
        axes2[0].set_ylabel(f"Cantidad ({', '.join(sorted(set(map(str, unidades))))})")

    colores_h = ["#d9534f" if e in {"AGOTADO", "ACTIVA"} else "#9370db" for e in estados]
    axes2[1].bar(etiquetas, holgura, color=colores_h)
    axes2[1].set_title("Holguras (rojo = cuello de botella)")
    axes2[1].set_ylabel("Holgura")
    if len(etiquetas) > 6:
        axes2[1].tick_params(axis="x", rotation=45)
    for i, (h, e) in enumerate(zip(holgura, estados)):
        if e in {"AGOTADO", "ACTIVA"}:
            axes2[1].text(i, h, " cuello", ha="center", va="bottom", fontsize=8, color="#d9534f")
    fig2.tight_layout()
    ruta2 = salida_dir / "grafico_recursos_y_holguras.png"
    fig2.savefig(ruta2, dpi=150)
    plt.close(fig2)
    rutas.append(ruta2)

    return rutas
