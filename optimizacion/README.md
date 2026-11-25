# Modulo de Optimizacion (PlanificaIO)

Motor generico de optimizacion con PuLP para mezcla de produccion industrial, configurable e interactivo. Incluye el Ejercicio 6 como caso de referencia y soporta n productos, m recursos, restricciones adicionales y tipos de variable por producto (Integer, Continuous, Binary).

## Requisitos
- Python 3.11+
- Dependencias: `optimizacion/requirements.txt`

## Instalacion
Desde la raiz del repositorio:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r optimizacion\requirements.txt
```

## Ejecucion

### Caso Ejercicio 6 (referencia)
```powershell
.\.venv\Scripts\python.exe -m optimizacion.main --modo ej6
```

### Menu interactivo (por defecto si no hay argumentos)
```powershell
.\.venv\Scripts\python.exe -m optimizacion.main
# o
.\.venv\Scripts\python.exe -m optimizacion.main --modo interactivo
```
Opciones del menu:
1. Ejecutar Ejercicio 6 (caso de referencia)
2. Modificar valores de un escenario existente (utilidades, disponibilidades, consumos, limites min/max, agregar/eliminar productos, recursos y restricciones adicionales) y guardar en JSON
3. Crear un ejercicio nuevo desde cero (interactivo)
4. Cargar escenario desde archivo externo `.json`

### Cargar escenario desde archivo JSON
```powershell
.\.venv\Scripts\python.exe -m optimizacion.main --archivo optimizacion\ejemplos\ejemplo_3x4_continuo.json
.\.venv\Scripts\python.exe -m optimizacion.main --archivo optimizacion\ejemplos\ejemplo_8x5_mixto.json
```

## Codigos de salida
- `0`: solucion optima valida y reportes exportados.
- `1`: error de validacion de entrada o carga de archivo.
- `2`: ejecucion sin solucion optima utilizable (`Infeasible`, `Unbounded`, `No optimo`, etc.).

## Formato de escenario (JSON)
- `PROBLEMA`: metadatos (`id`, `nombre`, `objetivo`: `maximizar|minimizar`).
- `PRODUCTO`: lista con `id`, `nombre`, `utilidad_unitaria`, `tipo_variable` (`Integer|Continuous|Binary`), `limite_inferior` (default 0), `limite_superior` (opcional).
- `RECURSO`: lista con `id`, `nombre`, `disponibilidad`, `unidad` (opcional).
- `CONSUMO_RECURSO`: matriz `{recurso_id: {producto_id: coeficiente}}`.
- `RESTRICCIONES_ADICIONALES`: lista con `id`, `nombre`, `coeficientes` por producto, `sentido` (`<=|>=|==`), `valor_derecho` (minimos/maximos por producto o grupo).
- `ESCENARIO_BASE` (opcional): `descripcion`, `produccion` por producto, `utilidad_reportada_enunciado`.

Tambien se soporta un formato generico con `VARIABLES`, `FUNCION_OBJETIVO` y `RESTRICCIONES` para integracion con otros orígenes.

## Clasificacion matematica (segun variables de decision de produccion)
- **PL/LP:** todas las variables de decision son `Continuous`.
- **PLE/IP:** todas las variables de decision son `Integer` o `Binary`. El Ejercicio 6 se clasifica como `PLE/IP`.
- **MILP:** mezcla de variables continuas con enteras/binarias.

Las variables de holgura de recursos (`y_r`) son auxiliares y no determinan la clasificacion.

## Salidas
En `optimizacion/outputs/` (cuando hay solucion optima):
- `resultados_productos.csv`
- `resultados_recursos.csv`
- `resultados_optimos.csv` (compatibilidad)
- `contexto_ia.json` (serializable para Django/React)
- `grafico_utilidad_y_produccion.png`
- `grafico_recursos_y_holguras.png`

## Pruebas
```powershell
.\.venv\Scripts\python.exe -m pytest -v optimizacion\tests\test_core.py
```

## Notas
- El analisis de sensibilidad es por **escenarios** (variacion configurable, por defecto ±10% de disponibilidad/RHS) mostrando impacto en Z y x_p; **no** corresponde a precios sombra/valores duales.
- Si el escenario base es infactible no se calcula porcentaje de mejora.
- La carpeta `backend/` no es modificada por este modulo.
