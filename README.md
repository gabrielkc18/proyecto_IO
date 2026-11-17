# PlanificaIO

Base frontend de PlanificaIO. La aplicación parte del prototipo React entregado y mantiene sus pantallas, flujos, componentes, datos demo y estilo visual. `prototype/planificaio_web_app.tsx` es una copia de referencia inalterada; el original de Descargas también se conserva sin cambios.

## Inicio

- Node.js 18 o superior
- `npm install`
- `npm run dev`
- `npm run build`

Stack: React 18, Vite, JavaScript, Tailwind CSS 3, Lucide React y Recharts. Los datos son demostrativos; no hay backend ni solver matemático real.

## Ramas y colaboración

La rama de integración prevista es `feature/mockup-planificaio`. El trabajo del integrante 1 debe quedar en `feature/mockup-integrante-1` y abrir un PR hacia la primera. No hacer commits de integración directamente a `main`. Al preparar este scaffold, el remoto indicado no expuso `main` ni `feature/mockup-planificaio`; solo se encontró `backend`, por lo que la rama de trabajo y el PR dependen de que el repositorio tenga esas ramas y permisos de escritura.

### Integrante 2: optimización

Trabajar en `src/pages/Optimization.jsx` y componentes/datos propios de optimización. Mantener el flujo de tres pasos y usar el contrato compartido siguiente; no crear una segunda navegación ni editar `src/App.jsx` salvo acuerdo con el integrante 1.

### Integrante 3: historial y análisis

Trabajar en `src/pages/History.jsx` y componentes/datos propios de historial. Consumir el estado compartido de resultados e historial; no duplicar navegación ni editar `src/App.jsx` salvo acuerdo con el integrante 1.

### Contrato de integración

- Navegación: `inicio`, `optimizacion`, `historial`, `perfil`, `ajustes`.
- Productos: `{ id, code, name, profit }[]`.
- Recursos: `{ id, name, unit, capacity }[]`.
- Consumos: `{ id, productId, resourceId, amount }[]`.
- Historial: cada ejecución conserva `id`, `date`, `name`, `profit`, `status`, `empiricalProfit`, `bottlenecks` y `producedItems`.
- Resultado actual: cantidades producidas, utilidad, uso de recursos, holguras, cuellos de botella y análisis demo.
- Notificaciones: usar la función común de notificación existente en la aplicación y mantener mensajes visuales consistentes.
- Componentes: crear los componentes compartidos en `src/components/common` y los de estructura en `src/components/layout`; evitar nombres y lógica duplicados.

Los componentes visuales comunes actuales (`NavItem`, `KPICard`, `ActivityItem`, `StepBadge`, `ThemeOption`, `ModalWrapper`) se exportan desde `src/components/common`. Las vistas pueden consumir los datos con `useSharedApp()` desde `src/context/SharedAppContext.jsx`; devuelve `activeTab`/`setActiveTab`, productos, recursos, consumos, historial, resultado actual y sus setters, además de `showNotification`. Para una vista nueva, recibir el contexto en la raíz y mantener los nombres de campos descritos arriba.

El prototipo actual concentra las vistas y el estado en `src/App.jsx` para preservar su comportamiento. Los directorios `pages`, `data`, `hooks`, `utils`, `context` y `components` son los puntos acordados para modularizar por entregas, trasladando una vista completa por vez y manteniendo el prototipo de referencia intacto. Al extraer una vista, el integrante responsable debe conservar props/contratos documentados y actualizar el README.
