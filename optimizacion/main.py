"""Script orquestador principal del modulo de optimizacion (CLI e interactivo)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Permite ejecutar como script: `python optimizacion/main.py`
if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from optimizacion.analytics.comparador import comparar_escenarios
from optimizacion.analytics.reportes import (
    asegurar_directorio_salida,
    exportar_contexto_ia,
    exportar_resultados_csv,
    generar_graficos,
    imprimir_tablas_consola,
)
from optimizacion.analytics.sensibilidad import analizar_sensibilidad_recursos
from optimizacion.core.datos_ejercicio6 import obtener_datos_ejercicio6
from optimizacion.core.gestor_escenarios import cargar_escenario_json, menu_interactivo
from optimizacion.core.motor_pulp import resolver_modelo


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="PlanificaIO - motor de optimizacion")
    p.add_argument("--modo", choices=["ej6", "interactivo"], help="Modo de ejecucion")
    p.add_argument("--archivo", help="Ruta a escenario JSON externo")
    p.add_argument("--no-sensibilidad", action="store_true", help="Omitir analisis de sensibilidad")
    return p.parse_args(argv)


def ejecutar_escenario(datos: dict, base_dir: Path, hacer_sensibilidad: bool = True) -> int:
    salida_dir = asegurar_directorio_salida(base_dir)
    resultado_optimo = resolver_modelo(datos)
    estado = (resultado_optimo.get("EJECUCION", {}) or {}).get("estado_proceso")

    if estado == "ERROR_VALIDACION":
        print("\nErrores de validacion detectados:")
        for e in resultado_optimo.get("errores", []):
            print(f"  - {e}")
        return 1

    comparacion = comparar_escenarios(datos, resultado_optimo)
    sensibilidad = (
        analizar_sensibilidad_recursos(datos)
        if hacer_sensibilidad
        else {
            "metodo": "analisis_escenarios_disponibilidad",
            "tipo_resultado": "escenarios",
            "interpretacion": "Analisis de sensibilidad omitido por parametro.",
            "utilidad_base": resultado_optimo.get("valor_objetivo"),
            "resultados_por_recurso": [],
            "recurso_mayor_impacto": None,
        }
    )
    imprimir_tablas_consola(resultado_optimo, comparacion, sensibilidad)

    if estado != "OPTIMO":
        print(f"\nEjecucion sin solucion optima utilizable: {estado}")
        return 2

    csv_paths = exportar_resultados_csv(resultado_optimo, salida_dir)
    json_path = exportar_contexto_ia(datos, resultado_optimo, comparacion, sensibilidad, salida_dir)
    graficos = generar_graficos(resultado_optimo, comparacion, salida_dir)

    print("\n=== ARCHIVOS GENERADOS ===")
    for c in csv_paths:
        print(f"- CSV: {c}")
    print(f"- JSON IA: {json_path}")
    for g in graficos:
        print(f"- Grafico: {g}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    base_dir = Path(__file__).resolve().parent

    datos = None
    if args.archivo:
        try:
            datos = cargar_escenario_json(args.archivo)
        except Exception as e:
            print(f"Error cargando archivo de escenario: {e}")
            return 1
    elif args.modo == "ej6":
        datos = obtener_datos_ejercicio6()
    elif args.modo == "interactivo":
        datos = menu_interactivo(base_dir)
        if datos is None:
            print("Operacion cancelada por el usuario.")
            return 0
    else:
        # Sin argumentos: menu interactivo por defecto
        datos = menu_interactivo(base_dir)
        if datos is None:
            print("Operacion cancelada por el usuario.")
            return 0

    return ejecutar_escenario(datos, base_dir, hacer_sensibilidad=not args.no_sensibilidad)


if __name__ == "__main__":
    raise SystemExit(main())
