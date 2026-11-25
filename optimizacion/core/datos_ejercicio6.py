"""Plantilla de configuracion de ejemplo: Ejercicio 6 (caso de referencia)."""

from __future__ import annotations

import copy
from typing import Any, Dict, List


def obtener_datos_ejercicio6() -> Dict[str, Any]:
    """Retorna la configuracion del Ejercicio 6 como plantilla de ejemplo.

    Clasificacion matematica: PLE/IP (todas las variables de decision de produccion son enteras).
    Las holguras de recursos son variables auxiliares implicitas y no determinan la clasificacion.
    """
    productos: List[Dict[str, Any]] = [
        {"id": "P1", "nombre": "Producto 1", "utilidad_unitaria": 80.0, "tipo_variable": "Integer"},
        {"id": "P2", "nombre": "Producto 2", "utilidad_unitaria": 110.0, "tipo_variable": "Integer"},
        {"id": "P3", "nombre": "Producto 3", "utilidad_unitaria": 90.0, "tipo_variable": "Integer"},
        {"id": "P4", "nombre": "Producto 4", "utilidad_unitaria": 60.0, "tipo_variable": "Integer"},
        {"id": "P5", "nombre": "Producto 5", "utilidad_unitaria": 130.0, "tipo_variable": "Integer"},
    ]
    recursos: List[Dict[str, Any]] = [
        {"id": "MPA", "nombre": "Materia Prima A", "disponibilidad": 3000.0, "unidad": "kg"},
        {"id": "MPB", "nombre": "Materia Prima B", "disponibilidad": 2500.0, "unidad": "kg"},
        {"id": "HM", "nombre": "Horas de Maquinado", "disponibilidad": 1600.0, "unidad": "h"},
    ]
    consumos: Dict[str, Dict[str, float]] = {
        "MPA": {"P1": 4.0, "P2": 3.0, "P3": 5.0, "P4": 2.0, "P5": 6.0},
        "MPB": {"P1": 2.0, "P2": 5.0, "P3": 3.0, "P4": 4.0, "P5": 4.0},
        "HM": {"P1": 3.0, "P2": 2.0, "P3": 4.0, "P4": 1.0, "P5": 5.0},
    }

    return copy.deepcopy(
        {
            "PROBLEMA": {
                "id": "EJ6",
                "nombre": "Ejercicio 6 - Maximizacion de utilidad",
                "objetivo": "maximizar",
                "descripcion": "Optimizacion de mezcla de produccion industrial (caso de referencia).",
            },
            "PRODUCTO": productos,
            "RECURSO": recursos,
            "CONSUMO_RECURSO": consumos,
            "RESTRICCIONES_ADICIONALES": [],
            "ESCENARIO_BASE": {
                "descripcion": "Escenario empirico de referencia: 150 unidades por producto",
                "produccion": {"P1": 150.0, "P2": 150.0, "P3": 150.0, "P4": 150.0, "P5": 150.0},
                "utilidad_reportada_enunciado": 64500.0,
            },
        }
    )
