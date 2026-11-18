# Módulo de optimización demostrativa

El flujo de Optimización conserva el editor compartido de productos, recursos y consumos. El paso 2 ejecuta un escenario demostrativo fijo (P1=100, P2=100, P3=50, P4=100, P5=50); no resuelve un modelo de programación lineal ni representa una mezcla óptima. Si los datos editados hacen que el ejemplo exceda una capacidad, la ejecución se detiene y muestra qué recurso revisar.

Con los datos de referencia del Ejercicio 6, el ejemplo produce una utilidad de $36.000, usa 1.450 kg de A, 1.450 kg de B y 1.050 h de maquinado. Las holguras respectivas son 1.550 kg, 1.050 kg y 550 h. La utilidad y los indicadores se calculan de nuevo con `products`, `resources` y `consumptions` al ejecutar.

## Contrato del resultado

`currentResult` queda preparado para que una integración futura reemplace el escenario demostrativo con un resultado del backend:

- `solverStatus`: estado legible del cálculo (actualmente `demostrativo`).
- `profit`: utilidad calculada para las cantidades recibidas.
- `produced`: producto, cantidad y utilidad por producto.
- `resourceUsage`: capacidad, consumo, holgura y condición de cuello de botella.
- `bottlenecks`: nombres de recursos agotados.
- `isDemonstration`: identifica expresamente el resultado actual.

La interpretación de IA se presenta como texto demostrativo derivado del resultado. No se llama a PuLP, al backend ni a un servicio de IA. El botón Exportar conserva su lugar en la experiencia, informa que es demostrativo y no afirma crear un archivo.

`OptimizationExecution`, `OptimizationResults` y `OptimizationHistory` están en `src/components/optimization/OptimizationModule.jsx`. El stepper, el estado compartido y el editor de entradas permanecen en `src/App.jsx`.
