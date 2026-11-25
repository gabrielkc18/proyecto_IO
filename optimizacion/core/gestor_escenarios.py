"""Gestor de escenarios para PlanificaIO (carga, edicion y creacion interactiva/CLI)."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .datos_ejercicio6 import obtener_datos_ejercicio6


def cargar_escenario_json(ruta: str | Path) -> Dict[str, Any]:
    path = Path(ruta)
    with path.open("r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("El archivo JSON debe contener un objeto de escenario.")
    return data


def guardar_escenario_json(datos: Dict[str, Any], ruta: str | Path) -> Path:
    path = Path(ruta)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    return path


def _input(prompt: str, default: Optional[str] = None, input_fn: Callable[[str], str] = input) -> str:
    s = input_fn(prompt)
    if s is None:
        s = ""
    s = str(s).strip()
    if s == "" and default is not None:
        return str(default)
    return s


def _ask_float(prompt: str, default: Optional[float] = None, allow_none: bool = False, input_fn=input) -> Optional[float]:
    while True:
        d = None if default is None else str(default)
        s = _input(prompt, d, input_fn=input_fn)
        if allow_none and s.lower() in {"", "none", "null"}:
            return None
        try:
            return float(s)
        except Exception:
            print("  Valor numerico invalido, intente de nuevo.")


def _ask_int(prompt: str, default: Optional[int] = None, input_fn=input) -> int:
    while True:
        d = None if default is None else str(default)
        s = _input(prompt, d, input_fn=input_fn)
        try:
            return int(s)
        except Exception:
            print("  Valor entero invalido, intente de nuevo.")


def _ensure_base_structure(datos: Dict[str, Any]) -> Dict[str, Any]:
    datos = copy.deepcopy(datos)
    datos.setdefault("PROBLEMA", {"id": "ESCENARIO", "nombre": "Escenario", "objetivo": "maximizar"})
    datos.setdefault("PRODUCTO", [])
    datos.setdefault("RECURSO", [])
    datos.setdefault("CONSUMO_RECURSO", {})
    datos.setdefault("RESTRICCIONES_ADICIONALES", [])
    return datos


def _print_resumen(datos: Dict[str, Any]) -> None:
    prods = datos.get("PRODUCTO", []) or []
    recs = datos.get("RECURSO", []) or []
    extras = datos.get("RESTRICCIONES_ADICIONALES", []) or []
    print(f"  Productos ({len(prods)}): {[p.get('id') for p in prods]}")
    print(f"  Recursos ({len(recs)}): {[r.get('id') for r in recs]}")
    print(f"  Restricciones adicionales: {len(extras)}")


def _asegurar_fila_consumos(datos: Dict[str, Any], rid: str) -> None:
    datos.setdefault("CONSUMO_RECURSO", {})
    datos["CONSUMO_RECURSO"].setdefault(rid, {})
    for p in datos.get("PRODUCTO", []) or []:
        pid = p.get("id")
        datos["CONSUMO_RECURSO"][rid].setdefault(pid, 0.0)


def _asegurar_columna_consumos(datos: Dict[str, Any], pid: str) -> None:
    datos.setdefault("CONSUMO_RECURSO", {})
    for r in datos.get("RECURSO", []) or []:
        rid = r.get("id")
        datos["CONSUMO_RECURSO"].setdefault(rid, {})
        datos["CONSUMO_RECURSO"][rid].setdefault(pid, 0.0)


def editar_escenario_interactivo(datos: Dict[str, Any], input_fn: Callable[[str], str] = input) -> Dict[str, Any]:
    datos = _ensure_base_structure(datos)
    while True:
        print("\n--- Editor de escenario ---")
        _print_resumen(datos)
        print("1) Editar utilidad de producto")
        print("2) Editar tipo/cotas de producto (Integer/Continuous/Binary, min/max)")
        print("3) Editar disponibilidad de recurso")
        print("4) Editar consumo recurso-producto")
        print("5) Agregar producto")
        print("6) Agregar recurso")
        print("7) Agregar restriccion adicional (<=, >=, ==)")
        print("8) Guardar escenario en JSON")
        print("9) Volver")
        op = _input("Opcion: ", input_fn=input_fn)
        if op == "1":
            pid = _input("ID producto: ", input_fn=input_fn)
            prod = next((p for p in datos.get("PRODUCTO", []) if str(p.get("id")) == pid), None)
            if not prod:
                print("  Producto no encontrado.")
                continue
            prod["utilidad_unitaria"] = _ask_float("Nueva utilidad: ", float(prod.get("utilidad_unitaria", 0.0)), input_fn=input_fn)
        elif op == "2":
            pid = _input("ID producto: ", input_fn=input_fn)
            prod = next((p for p in datos.get("PRODUCTO", []) if str(p.get("id")) == pid), None)
            if not prod:
                print("  Producto no encontrado.")
                continue
            tipo = _input("Tipo (Integer/Continuous/Binary): ", str(prod.get("tipo_variable", "Continuous")), input_fn=input_fn)
            prod["tipo_variable"] = tipo
            prod["limite_inferior"] = _ask_float("Limite inferior (min_produccion, default 0): ", float(prod.get("limite_inferior", 0.0) or 0.0), input_fn=input_fn)
            prod["limite_superior"] = _ask_float("Limite superior (max_produccion, vacio=None): ", None, allow_none=True, input_fn=input_fn)
        elif op == "3":
            rid = _input("ID recurso: ", input_fn=input_fn)
            rec = next((r for r in datos.get("RECURSO", []) if str(r.get("id")) == rid), None)
            if not rec:
                print("  Recurso no encontrado.")
                continue
            rec["disponibilidad"] = _ask_float("Nueva disponibilidad: ", float(rec.get("disponibilidad", 0.0)), input_fn=input_fn)
        elif op == "4":
            rid = _input("ID recurso: ", input_fn=input_fn)
            pid = _input("ID producto: ", input_fn=input_fn)
            if rid not in datos.get("CONSUMO_RECURSO", {}):
                print("  Recurso no encontrado en matriz.")
                continue
            if pid not in datos["CONSUMO_RECURSO"][rid]:
                print("  Producto no encontrado en matriz.")
                continue
            datos["CONSUMO_RECURSO"][rid][pid] = _ask_float("Nuevo consumo: ", float(datos["CONSUMO_RECURSO"][rid][pid]), input_fn=input_fn)
        elif op == "5":
            pid = _input("Nuevo ID producto: ", input_fn=input_fn)
            if any(str(p.get("id")) == pid for p in datos.get("PRODUCTO", [])):
                print("  Ya existe ese producto.")
                continue
            nombre = _input("Nombre: ", pid, input_fn=input_fn)
            util = _ask_float("Utilidad unitaria: ", 0.0, input_fn=input_fn)
            tipo = _input("Tipo (Integer/Continuous/Binary): ", "Continuous", input_fn=input_fn)
            lim_inf = _ask_float("Limite inferior (default 0): ", 0.0, input_fn=input_fn)
            lim_sup = _ask_float("Limite superior (vacio=None): ", None, allow_none=True, input_fn=input_fn)
            datos.setdefault("PRODUCTO", []).append({
                "id": pid, "nombre": nombre, "utilidad_unitaria": util,
                "tipo_variable": tipo, "limite_inferior": lim_inf, "limite_superior": lim_sup,
            })
            _asegurar_columna_consumos(datos, pid)
            # pedir consumos para recursos existentes
            for r in datos.get("RECURSO", []) or []:
                rid = r.get("id")
                datos["CONSUMO_RECURSO"].setdefault(rid, {})
                datos["CONSUMO_RECURSO"][rid][pid] = _ask_float(f"  Consumo {rid}->{pid}: ", 0.0, input_fn=input_fn)
        elif op == "6":
            rid = _input("Nuevo ID recurso: ", input_fn=input_fn)
            if any(str(r.get("id")) == rid for r in datos.get("RECURSO", [])):
                print("  Ya existe ese recurso.")
                continue
            nombre = _input("Nombre: ", rid, input_fn=input_fn)
            disp = _ask_float("Disponibilidad: ", 0.0, input_fn=input_fn)
            unidad = _input("Unidad (opcional): ", "", input_fn=input_fn)
            rec = {"id": rid, "nombre": nombre, "disponibilidad": disp}
            if unidad:
                rec["unidad"] = unidad
            datos.setdefault("RECURSO", []).append(rec)
            _asegurar_fila_consumos(datos, rid)
            for p in datos.get("PRODUCTO", []) or []:
                pid = p.get("id")
                datos["CONSUMO_RECURSO"][rid][pid] = _ask_float(f"  Consumo {rid}->{pid}: ", 0.0, input_fn=input_fn)
        elif op == "7":
            eid = _input("ID restriccion adicional: ", f"EXTRA_{len(datos.get('RESTRICCIONES_ADICIONALES', []))+1}", input_fn=input_fn)
            sentido = _input("Sentido (<=, >=, ==): ", "<=", input_fn=input_fn)
            rhs = _ask_float("Valor derecho: ", 0.0, input_fn=input_fn)
            coefs: Dict[str, float] = {}
            print("  Coeficientes por producto (enter para 0):")
            for p in datos.get("PRODUCTO", []) or []:
                pid = p.get("id")
                c = _ask_float(f"    coef {pid}: ", 0.0, input_fn=input_fn)
                if c is not None and abs(float(c)) > 0:
                    coefs[pid] = float(c)
            datos.setdefault("RESTRICCIONES_ADICIONALES", []).append(
                {"id": eid, "nombre": eid, "coeficientes": coefs, "sentido": sentido, "valor_derecho": rhs}
            )
        elif op == "8":
            ruta = _input("Ruta destino (.json): ", "optimizacion/ejemplos/escenario_editado.json", input_fn=input_fn)
            p = guardar_escenario_json(datos, ruta)
            print(f"  Guardado en: {p}")
        elif op == "9":
            return datos
        else:
            print("  Opcion invalida.")


def crear_escenario_interactivo(input_fn: Callable[[str], str] = input) -> Dict[str, Any]:
    print("\n--- Crear nuevo escenario ---")
    pid_prob = _input("ID problema: ", "NUEVO", input_fn=input_fn)
    nombre_prob = _input("Nombre problema: ", "Nuevo problema", input_fn=input_fn)
    objetivo = _input("Objetivo (maximizar/minimizar): ", "maximizar", input_fn=input_fn)

    n = _ask_int("Cantidad de productos (n): ", 1, input_fn=input_fn)
    m = _ask_int("Cantidad de recursos (m): ", 1, input_fn=input_fn)

    productos = []
    for i in range(n):
        print(f"  Producto {i+1}/{n}")
        pid = _input("    ID: ", f"P{i+1}", input_fn=input_fn)
        nombre = _input("    Nombre: ", pid, input_fn=input_fn)
        util = _ask_float("    Utilidad unitaria: ", 0.0, input_fn=input_fn)
        tipo = _input("    Tipo (Integer/Continuous/Binary): ", "Continuous", input_fn=input_fn)
        lim_inf = _ask_float("    Limite inferior (default 0): ", 0.0, input_fn=input_fn)
        lim_sup = _ask_float("    Limite superior (vacio=None): ", None, allow_none=True, input_fn=input_fn)
        productos.append({
            "id": pid, "nombre": nombre, "utilidad_unitaria": util,
            "tipo_variable": tipo, "limite_inferior": lim_inf, "limite_superior": lim_sup,
        })

    recursos = []
    for j in range(m):
        print(f"  Recurso {j+1}/{m}")
        rid = _input("    ID: ", f"R{j+1}", input_fn=input_fn)
        nombre = _input("    Nombre: ", rid, input_fn=input_fn)
        disp = _ask_float("    Disponibilidad: ", 0.0, input_fn=input_fn)
        unidad = _input("    Unidad (opcional): ", "", input_fn=input_fn)
        rec = {"id": rid, "nombre": nombre, "disponibilidad": disp}
        if unidad:
            rec["unidad"] = unidad
        recursos.append(rec)

    consumos: Dict[str, Dict[str, float]] = {}
    print("  Matriz de consumos:")
    for r in recursos:
        rid = r["id"]
        consumos[rid] = {}
        for p in productos:
            pid = p["id"]
            consumos[rid][pid] = _ask_float(f"    Consumo {rid}->{pid}: ", 0.0, input_fn=input_fn) or 0.0

    restricciones_extra = []
    k = _ask_int("Cantidad de restricciones adicionales: ", 0, input_fn=input_fn)
    for i in range(max(0, k)):
        eid = _input(f"  ID restriccion extra {i+1}: ", f"EXTRA_{i+1}", input_fn=input_fn)
        sentido = _input("    Sentido (<=, >=, ==): ", "<=", input_fn=input_fn)
        rhs = _ask_float("    Valor derecho: ", 0.0, input_fn=input_fn)
        coefs = {}
        for p in productos:
            c = _ask_float(f"    coef {p['id']}: ", 0.0, input_fn=input_fn)
            if c is not None and abs(float(c)) > 0:
                coefs[p["id"]] = float(c)
        restricciones_extra.append({"id": eid, "nombre": eid, "coeficientes": coefs, "sentido": sentido, "valor_derecho": rhs})

    escenario_base = None
    if _input("Definir escenario base para comparar? (s/n): ", "n", input_fn=input_fn).lower().startswith("s"):
        desc = _input("  Descripcion: ", "Escenario base", input_fn=input_fn)
        prod_base = {}
        for p in productos:
            prod_base[p["id"]] = _ask_float(f"  Produccion base {p['id']}: ", 0.0, input_fn=input_fn) or 0.0
        utilidad_rep = _ask_float("  Utilidad reportada enunciado (0 si no aplica): ", 0.0, input_fn=input_fn) or 0.0
        escenario_base = {"descripcion": desc, "produccion": prod_base, "utilidad_reportada_enunciado": utilidad_rep}

    datos = {
        "PROBLEMA": {"id": pid_prob, "nombre": nombre_prob, "objetivo": objetivo},
        "PRODUCTO": productos,
        "RECURSO": recursos,
        "CONSUMO_RECURSO": consumos,
        "RESTRICCIONES_ADICIONALES": restricciones_extra,
    }
    if escenario_base:
        datos["ESCENARIO_BASE"] = escenario_base
    return datos


def menu_interactivo(base_dir: Path, input_fn: Callable[[str], str] = input) -> Optional[Dict[str, Any]]:
    """Menu principal interactivo. Retorna escenario seleccionado/creado o None si salir."""
    while True:
        print("\n=== PlanificaIO - Motor de Optimizacion ===")
        print("1) Ejecutar Ejercicio 6 (caso de referencia)")
        print("2) Modificar valores de un escenario existente")
        print("3) Crear un ejercicio nuevo desde cero")
        print("4) Cargar escenario desde archivo externo (.json)")
        print("5) Salir")
        op = _input("Seleccione una opcion: ", input_fn=input_fn)
        if op == "1":
            return obtener_datos_ejercicio6()
        elif op == "2":
            print("  a) Partir de Ejercicio 6")
            print("  b) Partir de archivo JSON existente")
            sub = _input("  Seleccione: ", "a", input_fn=input_fn).lower()
            if sub == "b":
                ruta = _input("  Ruta JSON: ", input_fn=input_fn)
                try:
                    datos = cargar_escenario_json(ruta)
                except Exception as e:
                    print(f"  Error cargando archivo: {e}")
                    continue
            else:
                datos = obtener_datos_ejercicio6()
            datos = editar_escenario_interactivo(datos, input_fn=input_fn)
            if _input("Ejecutar este escenario ahora? (s/n): ", "s", input_fn=input_fn).lower().startswith("s"):
                return datos
        elif op == "3":
            datos = crear_escenario_interactivo(input_fn=input_fn)
            if _input("Guardar escenario en JSON? (s/n): ", "n", input_fn=input_fn).lower().startswith("s"):
                ruta = _input("Ruta destino: ", "optimizacion/ejemplos/escenario_nuevo.json", input_fn=input_fn)
                try:
                    p = guardar_escenario_json(datos, ruta)
                    print(f"  Guardado en: {p}")
                except Exception as e:
                    print(f"  Error guardando: {e}")
            return datos
        elif op == "4":
            ruta = _input("Ruta del archivo .json: ", input_fn=input_fn)
            try:
                return cargar_escenario_json(ruta)
            except Exception as e:
                print(f"  Error cargando archivo: {e}")
        elif op == "5":
            return None
        else:
            print("  Opcion invalida.")
