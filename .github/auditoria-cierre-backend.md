# Auditoría integral de cierre del backend — PlanificaIO

## Propósito

Realizar una auditoría técnica integral del backend de PlanificaIO para determinar, con evidencia del repositorio, qué falta para considerar terminado el backend.

**Esta tarea es exclusivamente de auditoría. No implementes funcionalidades ni modifiques código durante esta revisión.** El resultado debe ser un informe que sirva como plan definitivo de cierre del backend.

Lee primero `.github/copilot-instructions.md` y respeta todas sus reglas, especialmente las relacionadas con Git y GitHub.

## 1. Estado de Git y protección del trabajo

Antes de inspeccionar:

1. Ejecuta `pwd`.
2. Ejecuta `git status -sb`.
3. Ejecuta `git log -5 --oneline`.
4. Identifica la raíz del repositorio y el directorio `backend/`.
5. Comprueba si hay cambios locales sin commit.

El último commit conocido de la rama `backend` es:

`3cbc060 feat: implement workspace member management`

En el último estado comunicado por el usuario, la rama estaba un commit por delante de `origin/backend` y existía un directorio `.github/` sin seguimiento. **Este dato es histórico: verifica el estado real antes de sacar conclusiones.**

Reglas innegociables:

- No ejecutes `git add`, `git commit`, `git push`, `git pull`, `git merge`, `git rebase` ni ninguna operación que publique o sincronice cambios.
- No crees ramas, tags, releases ni pull requests.
- No modifiques, crees, elimines ni sobrescribas archivos del proyecto durante esta auditoría.
- No ejecutes migraciones sobre bases de datos con información real.
- No uses comandos destructivos (`reset --hard`, `clean -fd`, `restore`, etc.).
- No alteres tests ni sus expectativas para hacer que pasen.
- Puedes leer archivos, consultar el historial y ejecutar comprobaciones no destructivas. Si una comprobación requiere modificar archivos, instalar dependencias o cambiar configuración, no la ejecutes: indícala como pendiente y explica por qué.
- Conserva íntegros todos los cambios locales preexistentes.

## 2. Alcance de la auditoría

Inspecciona todas las aplicaciones, modelos, serializers, vistas, URLs, permisos, autenticación, servicios, integraciones, pruebas y configuración del repositorio.

Evalúa como mínimo estas doce áreas:

1. Seguridad y autenticación.
2. Gestión de usuarios y workspaces.
3. Aislamiento multi-tenant y RBAC.
4. CRUD y reglas de negocio.
5. Motor de optimización.
6. Integración con inteligencia artificial.
7. Persistencia y consistencia de datos.
8. Manejo de errores y validaciones.
9. Rendimiento y consultas a la base de datos.
10. Documentación de API.
11. Pruebas unitarias, de integración y de seguridad.
12. Preparación para producción y despliegue.

No te limites a buscar nombres de archivos o clases. Lee las implementaciones y sigue las relaciones entre modelos, serializers, vistas, servicios, permisos y rutas.

## 3. Clasificación obligatoria

Para cada área, módulo y funcionalidad relevante utiliza exactamente uno de estos estados:

- **Implementado y verificado:** existe implementación y hay evidencia suficiente de funcionamiento mediante pruebas o comprobaciones.
- **Implementado parcialmente:** existe código, pero faltan casos, controles, pruebas o integración.
- **No implementado:** no existe implementación funcional identificable.
- **No verificable con la evidencia disponible:** no es posible confirmar el estado por falta de entorno, configuración, secretos, servicios externos o evidencia.

No confundas «existe código» con «está verificado». No marques una funcionalidad como terminada solo porque existe un endpoint o una prueba aislada.

Para cada conclusión indica la evidencia concreta: archivo, clase, método, endpoint, prueba o comando. Si es posible, proporciona rutas y nombres exactos. No inventes números de línea.

## 4. Áreas que debes revisar

### 4.1 Seguridad y autenticación

Comprueba:

- Configuración de autenticación y permisos predeterminados de DRF.
- JWT: emisión, expiración, renovación y validación.
- Protección de endpoints privados.
- Registro, inicio de sesión, perfil y gestión de contraseñas, si existen.
- Gestión de usuarios inactivos.
- Protección de secretos y variables de entorno.
- `DEBUG`, `ALLOWED_HOSTS`, CORS y CSRF según el despliegue.
- Exposición de información sensible en errores y logs.
- Validación de entradas y controles contra abuso.

### 4.2 Usuarios y workspaces

Comprueba:

- Modelo de usuario realmente configurado.
- Creación de workspaces y membresía OWNER.
- Coherencia entre `Workspace.propietario` y `WorkspaceMembership` con rol OWNER.
- Gestión de miembros: listar, agregar, cambiar rol y retirar.
- Transferencia de propiedad y atomicidad.
- Restricciones de integridad y protección en Django Admin.
- Comportamiento ante usuarios inexistentes o inactivos.
- Reglas por rol y límites de ADMIN.

### 4.3 Multi-tenancy y RBAC

Comprueba el aislamiento en:

- Listados.
- Detalles por ID.
- Filtros.
- Creación y modificación.
- Eliminación.
- Acciones personalizadas.
- Ejecuciones.
- Resultados.
- Análisis IA.
- Endpoints de administración de miembros.

Comprueba que no se confíe en identificadores de workspace enviados por el cliente y que se valide la membresía del usuario autenticado.

### 4.4 CRUD y reglas de negocio

Revisa los módulos de problemas, productos, recursos y consumos:

- Operaciones implementadas.
- Validaciones de campos.
- Restricciones de unicidad y valores.
- Coherencia entre relaciones.
- Casos límite.
- Errores HTTP.
- Aislamiento entre workspaces.

### 4.5 Motor de optimización

Revisa la formulación matemática y el flujo de ejecución con PuLP/CBC:

- Variables de decisión.
- Funciones objetivo de maximización y minimización.
- Restricciones.
- Datos inválidos o incompletos.
- Soluciones óptimas.
- Problemas inviables, no acotados o sin solución.
- Errores del solver y estados de ejecución.
- Persistencia y consistencia de resultados.
- Límites de tiempo y manejo de fallos.

No concluyas que el modelo matemático es correcto sin seguir la formulación y las pruebas disponibles. Señala qué casos no están cubiertos.

### 4.6 Inteligencia artificial

Revisa la integración con Groq:

- Configuración de API keys.
- Manejo de errores, respuestas inválidas y timeouts.
- Contexto enviado al proveedor.
- Límites y fallos del servicio externo.
- Persistencia de análisis.
- Relación con ejecuciones y workspaces.
- Protección de datos y secretos.
- Pruebas que no dependan indebidamente de llamadas reales.

### 4.7 Persistencia y consistencia

Comprueba:

- Relaciones y `on_delete`.
- Constraints e índices.
- Migraciones y estado del esquema.
- Integridad entre entidades relacionadas.
- Transacciones en operaciones compuestas.
- Riesgo de estados parciales.
- Diferencias relevantes entre SQLite de desarrollo/pruebas y una posible base de datos de producción.

No afirmes que SQLite garantiza bloqueos de fila equivalentes a PostgreSQL. Identifica los límites del motor configurado.

### 4.8 Errores y validaciones

Revisa:

- Validaciones en serializers y modelos.
- Excepciones manejadas.
- Respuestas HTTP consistentes.
- Mensajes de error que no filtren información interna.
- Errores de proveedores externos y del solver.
- Casos de datos inválidos, inexistentes o no autorizados.

### 4.9 Rendimiento

Inspecciona consultas y posibles problemas:

- `select_related` y `prefetch_related` cuando correspondan.
- Consultas repetidas y N+1.
- Filtros e índices.
- Paginación.
- Límites de resultados.
- Operaciones costosas o síncronas.
- Riesgos de consumo excesivo de recursos.

No optimices ni modifiques código; solo documenta los hallazgos y su impacto.

### 4.10 Documentación de API

Comprueba si existe OpenAPI/Swagger u otra documentación:

- Cobertura de endpoints.
- Esquemas de entrada y salida.
- JWT.
- Header `X-Workspace-ID`.
- Permisos por rol.
- Códigos de error.
- Coherencia entre documentación y rutas reales.

### 4.11 Pruebas

Inspecciona la suite y determina qué cubre realmente:

- Pruebas unitarias.
- Pruebas de API.
- Integración del solver.
- Integración IA.
- Autenticación.
- RBAC.
- Aislamiento cross-workspace.
- Administración de miembros.
- Transferencia y rollback.
- Errores y casos límite.

Distingue cobertura existente de cobertura ausente. No inventes un porcentaje de cobertura si no se ha medido.

### 4.12 Producción y despliegue

Comprueba:

- Configuración por entorno.
- Variables de entorno y secretos.
- Base de datos de producción.
- Migraciones.
- Servidor WSGI/ASGI.
- Archivos estáticos.
- Logging.
- Health checks.
- CORS/CSRF/HTTPS.
- Dependencias y versiones.
- Instrucciones reproducibles de instalación y despliegue.
- Copias de seguridad y recuperación, si están documentadas.

No despliegues ni crees infraestructura.

## 5. Comprobaciones permitidas

Desde el directorio `backend/`, puedes ejecutar comprobaciones no destructivas si el entorno ya está preparado:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py showmigrations
python manage.py test -v 2
```

También puedes ejecutar:

```bash
git diff --check
git status -sb
git diff --stat
```

Antes de ejecutar la suite completa, revisa si los tests llaman a servicios externos o requieren credenciales. No provoques llamadas pagadas o cambios en servicios reales. Si no puedes ejecutar una comprobación de forma segura, indícala como no verificable y explica el motivo.

No instales dependencias ni cambies configuración para forzar una comprobación. Registra la limitación.

## 6. Formato del informe final

Entrega un informe técnico estructurado con estas secciones:

### A. Resumen ejecutivo
- Estado general del backend.
- Qué está sólido y verificado.
- Qué impide considerarlo terminado.
- Riesgos más importantes.

### B. Matriz de estado
Una tabla con las doce áreas del alcance, estado obligatorio, evidencia y observaciones.

### C. Estado por aplicación
Para cada aplicación Django:
- Responsabilidad.
- Modelos y relaciones relevantes.
- Endpoints.
- Permisos y aislamiento.
- Pruebas existentes.
- Estado y hallazgos.

### D. Hallazgos
Para cada problema:
- Identificador.
- Descripción.
- Evidencia concreta.
- Impacto.
- Probabilidad o condiciones de ocurrencia, si se pueden fundamentar.
- Severidad: crítica, alta, media o baja.
- Recomendación.

No exageres la severidad ni presentes hipótesis como vulnerabilidades confirmadas.

### E. Funcionalidades pendientes
Lista de trabajo pendiente, sin implementar nada, agrupada por:
- Seguridad.
- Integridad y reglas de negocio.
- Funcionalidad.
- Pruebas.
- Documentación.
- Producción.

### F. Dependencias y orden de trabajo
Propón un orden lógico de implementación. Identifica tareas bloqueantes y tareas que pueden desarrollarse independientemente.

### G. Criterios objetivos de cierre
Define condiciones verificables para declarar terminado el backend: pruebas, seguridad, documentación, configuración y comportamiento funcional.

### H. Evidencia de validación
Incluye comandos ejecutados, resultados reales, número de pruebas aprobadas/fallidas y comprobaciones que no pudieron realizarse.

### I. Estado Git
Indica:
- Rama.
- Commit actual.
- Estado de sincronización observado.
- Archivos locales modificados o sin seguimiento.
- Confirmación de que no se ejecutó ninguna operación Git remota ni se publicaron cambios.

## 7. Límites de esta tarea

- No implementes funcionalidades.
- No corrijas hallazgos.
- No refactorices.
- No crees ni modifiques documentación del proyecto.
- No crees archivos de informe dentro del repositorio.
- No modifiques tests.
- No generes migraciones.
- No hagas commits ni push.
- No publiques nada en GitHub.

El único resultado de esta tarea debe ser el informe en el chat de Copilot. Puedes recomendar un plan de implementación, pero no ejecutarlo.

## 8. Criterio de finalización

La auditoría termina cuando hayas revisado las doce áreas, las aplicaciones del backend y la evidencia disponible, y hayas entregado el informe completo con estados, hallazgos, riesgos, pendientes, prioridades y criterios de cierre.

Si una parte no puede verificarse, declárala explícitamente como **No verificable con la evidencia disponible**. No rellenes vacíos con suposiciones.

Al entregar el informe, detente y espera mi revisión. No continúes con ninguna implementación hasta recibir una nueva instrucción.

**Recuerda: esta misión es auditar y planificar, no programar. No hagas cambios en el repositorio ni publiques nada.**
