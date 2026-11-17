# MISIÓN MAESTRA — CIERRE TÉCNICO DEL BACKEND DE PLANIFICAIO

## 0. Tu misión

Trabaja directamente sobre el repositorio local de **PlanificaIO** para completar, endurecer, probar y documentar el backend, utilizando la auditoría integral ya realizada como punto de partida.

No quiero únicamente recomendaciones ni otro informe de diagnóstico. Quiero que ejecutes el trabajo técnico que esté suficientemente definido: inspeccionar, planificar internamente, implementar, probar, corregir regresiones y documentar.

Trabaja de forma autónoma por unidades funcionales hasta completar todo lo que pueda resolverse con las decisiones que ya están tomadas. No me consultes después de cada archivo o etapa. **Consúltame únicamente cuando hayas terminado todo el trabajo posible y necesites decisiones de producto que no estén definidas, o al entregar el informe final.**

La autonomía concedida permite modificar el repositorio local y ejecutar pruebas. No permite publicar ni sincronizar cambios.

Lee primero y respeta:
- `.github/copilot-instructions.md`
- Este documento.

Si ambos documentos parecen contradecirse, aplica siempre la regla más restrictiva en materia de seguridad, preservación de datos y Git/GitHub.

---

## 1. REGLAS INNEGOCIABLES DE GIT Y GITHUB

El usuario conserva el control de todos los cambios publicados.

**Está absolutamente prohibido ejecutar:**
- `git add`
- `git commit`
- `git push`
- `git pull`
- `git fetch`
- `git merge`
- `git rebase`
- `git cherry-pick`
- creación de ramas, tags, releases o pull requests
- cualquier operación que publique, sincronice o altere el repositorio remoto.

No publiques, subas ni sincronices absolutamente nada en GitHub.

Puedes inspeccionar `git status`, `git log`, `git diff`, `git show` y otras operaciones de lectura.

Puedes modificar archivos localmente dentro del alcance de esta misión. Al terminar, todos los cambios deben permanecer locales, sin commit.

No ejecutes comandos destructivos como:
- `git reset --hard`
- `git clean -fd`
- `git checkout --`
- `git restore` sobre cambios del usuario
- borrados masivos o restauraciones globales.

No sobrescribas ni elimines cambios preexistentes que no pertenezcan a esta misión. No alteres `.github/copilot-instructions.md`, los documentos de contexto existentes ni otros archivos del usuario salvo que sea indispensable y esté expresamente dentro del alcance.

El último commit conocido es:

`3cbc060 feat: implement workspace member management`

El último estado comunicado era la rama `backend`, un commit local por delante de `origin/backend` y el directorio `.github/` sin seguimiento. Es información histórica: inspecciona el estado real al iniciar. No intentes actualizar la referencia remota.

Los commits futuros deberán separarse por funcionalidad y pruebas. Al finalizar, sugiere una secuencia de commits pequeños, con rutas y mensajes concretos, pero no los crees.

---

## 2. DECISIONES DE PRODUCTO YA TOMADAS

Estas decisiones son requisitos confirmados. No las cambies unilateralmente.

### 2.1 Cuentas: registro público y creación administrativa

PlanificaIO tendrá ambas modalidades:

1. Registro público de usuarios.
2. Creación administrativa de usuarios.

Implementa flujos seguros y coherentes con el modelo de usuario existente. Antes de cambiar el modelo, inspecciona su configuración real. La auditoría encontró que se utiliza `django.contrib.auth.models.User`, con `username` como identificador y `email` no único.

Requisitos:
- No utilizar email como identificador único mientras el modelo no lo garantice.
- Validar username y contraseñas.
- No devolver ni almacenar contraseñas en texto claro.
- No exponer información que permita enumerar cuentas innecesariamente.
- Crear la cuenta, su workspace personal y la membresía OWNER dentro de una transacción.
- Evitar usuarios, workspaces o membresías parcialmente creados.
- Comprobar que no se dupliquen workspaces personales ni membresías.
- Respetar usuarios inactivos.
- Definir una forma segura de asignar credenciales en creación administrativa.
- No crear automáticamente workspaces adicionales al iniciar sesión.
- No conceder privilegios administrativos globales a usuarios registrados públicamente.

Inspecciona qué endpoints ya existen antes de crear otros. Implementa perfil, cambio de contraseña y recuperación de contraseña si faltan y son necesarios para ofrecer una gestión de cuentas completa. La recuperación debe diseñarse sin revelar si una cuenta existe. Si requiere correo, documenta y configura el mecanismo mediante variables de entorno; no inventes credenciales ni proveedores.

La verificación de correo puede quedar pendiente si no existe un servicio de correo configurado. En ese caso, implementa una base segura y documenta exactamente la dependencia externa faltante, sin fingir que se ha verificado el correo.

### 2.2 Base de datos de producción: PostgreSQL

PostgreSQL será el motor objetivo de producción.

SQLite puede seguir utilizándose para desarrollo local rápido si la arquitectura lo permite, pero PostgreSQL debe ser la referencia para validación de producción.

Requisitos:
- Añadir el driver adecuado y compatible con las versiones reales del proyecto.
- Configurar la conexión por variables de entorno.
- Separar claramente configuración de desarrollo, pruebas y producción.
- No incluir credenciales en el repositorio.
- Revisar tipos, constraints, índices, relaciones y migraciones.
- Probar migraciones en una base PostgreSQL de pruebas.
- Ejecutar la suite sobre PostgreSQL cuando exista un servicio disponible.
- Documentar cómo levantar PostgreSQL localmente y cómo configurar producción.
- No migrar ni modificar bases de datos con información real.
- No eliminar ni recrear bases de datos existentes.
- No afirmar que PostgreSQL fue probado si el servicio no estuvo disponible.

Con PostgreSQL, evalúa `transaction.atomic()` y `select_for_update()` para operaciones sensibles. Conserva constraints de integridad. No asumas que una transacción por sí sola resuelve todas las condiciones de carrera.

### 2.3 Minimización: decisión de negocio todavía pendiente

**No está definido qué debe minimizar el motor. No inventes esta semántica.**

La auditoría encontró que la implementación actual minimiza una expresión basada en utilidad unitaria, mientras que los valores son no negativos y no hay restricciones de demanda que eviten la solución trivial de producir cero.

No cambies la formulación ni afirmes que minimización está soportada correctamente hasta que el usuario defina su significado.

Puedes:
- Inspeccionar y documentar la formulación actual.
- Identificar las limitaciones matemáticas.
- Diseñar alternativas claramente diferenciadas.
- Preparar pruebas de aceptación propuestas, sin cambiar el comportamiento productivo.

No puedes:
- Interpretar utilidad como costo sin evidencia.
- Añadir campos de costo, demanda mínima u otras reglas de negocio por iniciativa propia.
- Cambiar la función objetivo de minimización de manera especulativa.

Deja esta parte identificada como **bloqueada por decisión de producto** y continúa con el resto del trabajo. En el informe final formula una pregunta concreta y presenta las alternativas y sus consecuencias.

### 2.4 Inteligencia artificial: consentimiento explícito antes de enviar datos a Groq

La utilización de IA es opcional. El usuario debe autorizar expresamente el envío de datos a Groq antes de cada análisis, o mediante un consentimiento persistente, claro, revocable y documentado si la arquitectura justifica esa modalidad. No presupongas consentimiento.

Requisitos:
- El consentimiento debe validarse en el backend, no solamente en React.
- Una solicitud sin consentimiento válido no puede invocar al proveedor.
- La optimización debe seguir funcionando sin IA.
- Informar claramente qué categorías de datos se enviarán.
- Minimizar los datos enviados.
- No enviar contraseñas, tokens, secretos ni datos personales que no sean necesarios.
- No incluir información sensible en prompts o logs.
- Manejar timeout, errores HTTP, límites y respuestas inválidas del proveedor.
- No duplicar llamadas por reintentos involuntarios.
- Registrar el consentimiento de forma proporcionada y auditable, evitando guardar datos innecesarios.
- Permitir revocar cualquier consentimiento persistente.
- Probar con mocks en la suite normal; no realizar llamadas pagadas a Groq en las pruebas rutinarias.
- No inventar ni exponer API keys.

Si no hay una política de privacidad o texto informativo disponible, crea una propuesta técnica claramente identificada para revisión; no afirmes que existe consentimiento legalmente válido sin revisión humana.

---

## 3. ESTADO TÉCNICO CONOCIDO: PUNTO DE PARTIDA

La auditoría anterior reportó:

- 191 pruebas aprobadas.
- `python manage.py check`: sin problemas.
- `python manage.py makemigrations --check --dry-run`: sin cambios pendientes.
- `git diff --check`: sin errores.
- Django 6.1.3.
- Django REST Framework 3.18.3.
- PuLP 4.2.0.
- CBC disponible mediante `COIN_CMD`.
- Pruebas de IA con proveedor simulado; no verificaron llamadas reales a Groq.
- SQLite como base configurada en el entorno auditado.
- No se midió cobertura.
- No se verificó un despliegue real de producción.

La auditoría identificó estos hallazgos principales:

1. Configuración de producción incompleta: `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`, HTTPS, cookies, logging y despliegue deben endurecerse.
2. Concurrencia de transferencia y membresías sin validación real sobre el motor de producción.
3. Minimización matemáticamente ambigua y posiblemente trivial.
4. Solver y llamadas IA síncronas, sin límites operativos suficientes demostrados.
5. Ausencia de API de registro, perfil y recuperación en el estado auditado.
6. Falta documentación OpenAPI/Swagger.
7. Exposición potencial de `mensaje_error` con detalles internos del solver.
8. Coherencia entre producto y recurso validada en aplicación, pero no garantizada en todos los caminos de escritura directa.
9. Privacidad y consentimiento para enviar contexto a Groq no resueltos.
10. Paginación, límites de entrada, health checks, observabilidad, backups y recuperación sin evidencia suficiente.
11. Acceso global de Django Admin a modelos que podrían requerir un modelo operativo más restringido.

Estos hallazgos son un punto de partida, no una verdad inmutable. Revalida cada uno contra el código actual. Si ya está corregido, no repitas el trabajo.

---

## 4. PROCEDIMIENTO DE INICIO Y PROTECCIÓN

Antes de modificar código:

1. Ejecuta `pwd`.
2. Ejecuta `git status -sb`.
3. Ejecuta `git log -5 --oneline --decorate`.
4. Identifica raíz del repositorio y directorio `backend/`.
5. Lee los dos documentos de instrucciones.
6. Inspecciona todos los cambios locales y archivos sin seguimiento.
7. Identifica qué cambios pertenecen a tareas anteriores y consérvalos.
8. Repite las comprobaciones base de manera segura si el entorno lo permite.

Si encuentras cambios locales ajenos a esta misión, no los incluyas en tus modificaciones ni los sobrescribas. Trabaja alrededor de ellos.

Antes de implementar, construye internamente un inventario de aplicaciones, modelos, endpoints, permisos, pruebas y dependencias. No te detengas a pedirme autorización para decisiones técnicas ordinarias que ya estén definidas aquí.

---

## 5. PLAN DE EJECUCIÓN OBLIGATORIO

Trabaja en las siguientes etapas, en este orden. Puedes continuar entre etapas sin pedirme aprobación, siempre que no exista una decisión de producto pendiente que bloquee la etapa.

### ETAPA 1 — Seguridad, multi-tenancy y consistencia

Audita y endurece:
- Autenticación JWT y permisos predeterminados.
- `WorkspaceContextMixin`.
- Roles OWNER, ADMIN, EDITOR y VIEWER.
- Listas, detalles, filtros y acciones personalizadas.
- Endpoints de ejecución, resultados e IA.
- Administración de miembros.
- Transferencia de propiedad.
- Django Admin.
- Coherencia entre `Workspace.propietario` y membresía OWNER.
- Coherencia de `ConsumoRecurso` entre producto y recurso.
- Escrituras por API, admin, ORM y servicios.

La transferencia debe conservar un único OWNER y sincronizar la FK y la membresía en la misma operación transaccional. El antiguo OWNER pasa a ADMIN según la regla acordada. El destinatario debe ser un miembro existente y activo del workspace.

Prueba permisos por rol, aislamiento, rollback y concurrencia en PostgreSQL cuando esté disponible. Para SQLite, documenta sus límites y no confíes en bloqueos de fila inexistentes.

No introduzcas constraints imposibles de expresar de forma portable sin analizar sus efectos en SQLite y PostgreSQL. Si una invariancia solo puede garantizarse mediante servicios transaccionales, centraliza los caminos de escritura y protege Django Admin.

### ETAPA 2 — Cuentas y autenticación

Implementa los flujos de registro público y creación administrativa con las reglas de la sección 2.1.

Incluye, si faltan:
- Registro público.
- Perfil de usuario.
- Cambio de contraseña.
- Recuperación de contraseña con respuesta que no revele existencia de cuenta.
- Validación de usuarios activos.
- Límites de intentos y throttling adecuado.
- Creación transaccional de workspace personal y OWNER.
- Pruebas de rollback y duplicidad.

No cambies el modelo de usuario ni hagas que email sea único sin una justificación arquitectónica y migración segura. Prefiere compatibilidad con el usuario actual.

### ETAPA 3 — PostgreSQL

Prepara configuración de PostgreSQL y pruebas reales sobre ese motor.

- Dependencia compatible.
- Variables de entorno.
- Settings separados.
- Migraciones revisadas.
- Constraints e índices revisados.
- Pruebas de transacciones y concurrencia.
- Documentación de instalación y ejecución.
- Suite completa sobre PostgreSQL si el entorno está disponible.

No borres datos ni migres una base real. Si PostgreSQL no está instalado o accesible, prepara la configuración y documentación, pero marca la validación de integración como no realizada. No instales servicios del sistema ni cambies infraestructura sin autorización.

### ETAPA 4 — Motor de optimización

Audita la formulación matemática y completa las pruebas para:
- Maximización.
- Datos inválidos.
- Problemas inviables.
- Problemas no acotados.
- Estados sin solución.
- Errores del solver.
- Límites de tiempo y dimensiones.
- Persistencia de ejecución y resultados.
- Consistencia de resultados.

La minimización permanece bloqueada por decisión de negocio. No alteres esa función objetivo hasta recibir la definición del usuario. En el informe final presenta alternativas, ecuaciones y ejemplos para que el usuario pueda decidir.

No cambies resultados matemáticos para hacer pasar pruebas. Justifica cada cambio con una regla de negocio verificable.

### ETAPA 5 — IA con consentimiento

Implementa el consentimiento explícito para análisis con Groq.

Asegura:
- Validación server-side.
- No invocar proveedor si no hay autorización.
- Contexto mínimo necesario.
- Exclusión de secretos y datos personales innecesarios.
- Manejo de timeout y errores.
- Protección frente a duplicación de llamadas.
- Registro proporcionado de consentimiento.
- Revocación si el consentimiento es persistente.
- Suite con mocks y pruebas que demuestren que sin consentimiento no hay llamada.

No realices llamadas reales ni pagadas en las pruebas rutinarias.

### ETAPA 6 — Errores, límites y rendimiento

Revisa:
- Paginación coherente.
- Límites de entrada y tamaño de problemas.
- Timeouts de solver y proveedor IA.
- Respuestas de error consistentes.
- Separación entre mensajes públicos y diagnóstico interno.
- Logging estructurado sin secretos.
- Consultas N+1.
- Uso de `select_related` y `prefetch_related`.
- Índices y filtros.
- Protección contra operaciones abusivas.

No introduzcas Celery, Redis u otra infraestructura por defecto. Solo propón o implementa una cola si la necesidad está demostrada y puede ejecutarse y probarse con la infraestructura disponible. Si requiere una decisión o servicio externo, documenta el bloqueo.

### ETAPA 7 — Documentación OpenAPI

Implementa documentación OpenAPI/Swagger si no existe, usando una dependencia compatible con las versiones reales.

Documenta todos los endpoints reales:
- Métodos.
- Rutas.
- Payloads.
- Respuestas.
- JWT.
- `X-Workspace-ID`.
- Roles y permisos.
- Paginación y filtros.
- Errores.
- Consentimiento de IA.

Verifica que la documentación se genere y corresponda al código. No documentes endpoints inexistentes.

### ETAPA 8 — Producción y despliegue

Prepara el backend para un despliegue reproducible:

- Settings de desarrollo, pruebas y producción.
- `DEBUG=False` en producción.
- `SECRET_KEY` obligatoria y segura.
- `ALLOWED_HOSTS` explícito.
- HTTPS y cookies seguras.
- CORS limitado a orígenes autorizados, si el frontend separado lo requiere.
- CSRF según el mecanismo de autenticación y arquitectura.
- PostgreSQL.
- Servidor WSGI/ASGI.
- Archivos estáticos.
- Logging.
- Health check sin exponer información sensible.
- Variables de entorno.
- Dependencias fijadas y reproducibles.
- Guía de instalación y despliegue.
- Procedimiento de backup y restore documentado y verificable en entorno de prueba.

No despliegues, no crees infraestructura, no compres servicios, no uses credenciales reales y no hagas operaciones contra producción.

No marques backups, restauración o despliegue como verificados si solo existe documentación.

### ETAPA 9 — Validación integral

Ejecuta pruebas focalizadas por etapa y luego la suite completa.

Comprueba:
- Autenticación y cuentas.
- RBAC y aislamiento.
- Workspaces y membresías.
- Integridad de relaciones.
- Solver y estados.
- Consentimiento IA.
- Errores y límites.
- PostgreSQL.
- OpenAPI.
- Configuración de producción.

No cambies las expectativas de tests para conseguir un resultado verde. Corrige el código o explica por qué el test está equivocado con evidencia.

---

## 6. PRUEBAS Y COMANDOS DE VALIDACIÓN

Desde `backend/`, ejecuta según corresponda:

```bash
python -m compileall -q apps config
python manage.py test -v 2
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py showmigrations
```

Ejecuta además:
- Suite completa sobre SQLite si sigue siendo el motor local.
- Suite completa sobre PostgreSQL cuando el servicio de pruebas esté disponible.
- Pruebas focalizadas de cada módulo modificado.
- Validación de generación OpenAPI.
- `git diff --check`.

No afirmes que se probaron dos motores si solo se probó uno.

No instales dependencias ni servicios del sistema sin autorización. Si falta una dependencia o servicio, documenta exactamente la limitación y continúa con las tareas que sí pueden realizarse.

No provoques llamadas pagadas a Groq ni a servicios externos en la suite normal.

---

## 7. CRITERIOS DE CALIDAD

En todo momento:

- Respeta la arquitectura actual.
- Reutiliza código antes de duplicarlo.
- No hagas refactorizaciones masivas sin necesidad.
- No cambies modelos o migraciones sin justificación.
- No elimines funcionalidades existentes.
- No ocultes errores.
- No expongas secretos.
- No confíes en datos enviados por el cliente para autorización.
- No confundas que un endpoint responda con que su comportamiento sea correcto.
- No confundas código implementado con código probado.
- No inventes porcentajes de cobertura.
- No declares seguridad absoluta.
- Mantén compatibilidad con las versiones reales del proyecto.
- Documenta decisiones técnicas y limitaciones.

Si una tarea depende de una decisión de negocio no definida, no inventes la respuesta: continúa con las demás tareas y deja esa parte bloqueada y claramente documentada.

Si aparece una operación irreversible, riesgo de pérdida de datos, cambio incompatible, necesidad de credenciales reales o instalación de infraestructura, no la ejecutes. Documenta qué autorización se necesita y continúa con el resto.

---

## 8. INFORME FINAL OBLIGATORIO

Cuando hayas completado todo lo que puede hacerse con las decisiones disponibles, detente y entrega un informe técnico en el chat con:

1. Resumen ejecutivo.
2. Estado de cada etapa.
3. Funcionalidades nuevas implementadas.
4. Funcionalidades existentes revisadas y conservadas.
5. Hallazgos corregidos.
6. Hallazgos que permanecen.
7. Archivos creados, modificados y eliminados, con justificación.
8. Modelos y migraciones modificados, si los hubo.
9. Endpoints nuevos o modificados.
10. Decisiones técnicas tomadas.
11. Pruebas ejecutadas, aprobadas y fallidas.
12. Resultados separados por motor de base de datos.
13. Resultado de `check`, migraciones, compileall, OpenAPI y `git diff --check`.
14. Tareas bloqueadas por decisiones de producto.
15. Dependencias externas o infraestructura que no pudieron verificarse.
16. Riesgos restantes.
17. Criterios de cierre todavía incumplidos.
18. Secuencia propuesta de commits pequeños, indicando archivos y mensajes.
19. Estado Git final: rama, commit actual, archivos modificados y archivos sin seguimiento.
20. Confirmación explícita de que no se ejecutó `git add`, commit, push, pull, fetch, merge, rebase ni ninguna publicación remota.

No afirmes que el backend está al 100 % si queda una decisión de negocio pendiente, una validación no ejecutada o un riesgo importante sin resolver.

Al terminar el informe, espera mi revisión. No continúes con otra tarea ni publiques nada.

---

## 9. DEFINICIÓN DE ÉXITO

El objetivo es dejar PlanificaIO con un backend funcionalmente completo respecto de los requisitos definidos, con:

- Gestión segura de cuentas y workspaces.
- Autenticación y autorización robustas.
- Aislamiento multi-tenant.
- Integridad de datos.
- PostgreSQL como motor objetivo de producción.
- Optimización matemática validada para los objetivos definidos.
- IA opcional con consentimiento explícito.
- Límites, errores y rendimiento controlados.
- API documentada.
- Configuración y procedimientos de producción reproducibles.
- Pruebas suficientes para demostrar los comportamientos críticos.

**Tu autonomía llega hasta modificar, probar y documentar localmente. La aceptación final, los commits y la publicación en GitHub siempre corresponden al usuario.**

Empieza inspeccionando el estado real del repositorio y continúa con las etapas en el orden establecido. No me entregues solo otro plan: ejecuta el trabajo posible, con rigor, hasta llegar al informe final.
