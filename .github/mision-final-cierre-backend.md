# MISIÓN FINAL — CERRAR Y VALIDAR EL BACKEND DE PLANIFICAIO

## Objetivo

Completa el backend de PlanificaIO hasta el máximo estado funcional y operativo que pueda verificarse con los recursos disponibles hoy. Trabaja directamente sobre el repositorio local: inspecciona el código, corrige defectos, completa pruebas, valida la configuración, documenta los procedimientos y deja una lista inequívoca de cualquier bloqueo externo o decisión de producto que impida declarar el cierre.

Esta misión continúa el trabajo que ya realizaste. **No reconstruyas ni reemplaces lo que ya funciona.** Revisa el estado actual y trabaja sobre los cambios locales existentes.

No me consultes por decisiones técnicas ordinarias ya establecidas. Trabaja autónomamente y pregunta solamente ante una decisión de negocio aún no definida, una operación destructiva, una instalación de sistema con privilegios, credenciales/servicios externos que no estén disponibles o un bloqueo que no puedas resolver con seguridad.

La meta es dejar el backend listo para que podamos comenzar el frontend React sin arrastrar problemas conocidos.

---

## 1. REGLAS ABSOLUTAS DE GIT/GITHUB

El usuario conserva el control de Git y de toda publicación.

**No ejecutes bajo ninguna circunstancia:**
- `git add`
- `git commit`
- `git push`
- `git pull`
- `git fetch`
- `git merge`
- `git rebase`
- `git cherry-pick`
- creación de ramas, tags, releases o pull requests
- publicación, sincronización o modificación del repositorio remoto.

No uses `git reset --hard`, `git clean -fd`, `git checkout --`, `git restore` sobre archivos modificados ni ningún comando destructivo equivalente.

Puedes leer `git status`, `git diff`, `git log`, `git show` y revisar los cambios.

Modifica solamente el repositorio local. No sobrescribas ni elimines cambios anteriores. No incluyas de forma accidental documentos o cambios preexistentes en tus modificaciones.

Los commits se realizarán posteriormente, bajo autorización expresa del usuario, separados por funcionalidad. Al final sugiere los grupos de commits con rutas y mensajes, pero no los prepares ni los crees.

---

## 2. CONTEXTO Y ESTADO DE PARTIDA

Lee íntegramente:
- `.github/copilot-instructions.md`
- `.github/mision-maestra-cierre-backend.md`
- Este documento.

El último commit conocido es:

`3cbc060 feat: implement workspace member management`

La misión anterior dejó estos resultados reportados:
- Suite completa: **216 pruebas aprobadas**.
- `compileall`: aprobado.
- `python manage.py check`: aprobado.
- `makemigrations --check --dry-run`: `No changes detected`.
- `git diff --check`: sin errores.
- Migraciones locales pendientes en `cuentas.0001_initial` y `inteligencia_artificial.0003` a `0006`.
- PostgreSQL no estaba corriendo y no se habían instalado `psycopg`/`psycopg2`.
- La generación de OpenAPI no se pudo verificar por dependencias faltantes (`inflection` y `uritemplate`).
- El correo SMTP real no se probó.
- No hubo despliegue ni prueba real de backup/restore.
- La minimización está pendiente de decisión de negocio.

**Estos datos son históricos. Verifica el estado actual antes de actuar.**

### Decisiones de producto confirmadas

1. Cuentas: habrá registro público y creación administrativa.
2. Base de datos objetivo de producción: PostgreSQL.
3. Minimización: todavía no está definida. No inventes la función objetivo.
4. Datos a Groq: el envío requiere consentimiento explícito del usuario, comprobado en backend.

### Acceso y contexto técnico

El repositorio local se encuentra en `~/proyectos/proyecto_IO`; backend en `backend/`; entorno virtual conocido: `backend/.venv`; sistema observado: Debian.

Versiones históricas observadas: Django 6.1.3, DRF 3.18.3, PuLP 4.2.0. Comprueba las versiones reales.

---

## 3. PRIMER PASO: REVISIÓN DE ESTADO Y CAMBIOS YA HECHOS

Antes de editar:
1. Ejecuta `pwd`, `git status -sb` y `git log -5 --oneline --decorate`.
2. Identifica la raíz y el backend.
3. Revisa el diff local completo y los archivos sin seguimiento.
4. Distingue cambios de la misión anterior, documentos `.github/` y cualquier cambio preexistente del usuario.
5. Conserva todos los cambios existentes.
6. Comprueba si existe ya la app `cuentas`, su migración, el consentimiento IA, el esquema OpenAPI, la configuración PostgreSQL, la paginación y la guía operativa.
7. Revisa si el usuario pulsó Keep y si el código actual coincide con el informe final de Copilot.

No ejecutes operaciones de Git que cambien el índice o el repositorio remoto.

No asumas que el informe anterior describe exactamente el estado actual. Valida el código.

---

## 4. RESOLVER Y VALIDAR POSTGRESQL — PRIORIDAD MÁXIMA

PostgreSQL es el motor de producción decidido por el usuario. La configuración sola no basta: necesitamos ejecutar pruebas reales.

### 4.1 Dependencias de Python

- Revisa `requirements.txt` y la dependencia del driver PostgreSQL.
- Comprueba si el entorno virtual tiene el driver.
- Instala, si hace falta, las dependencias declaradas del proyecto **únicamente dentro de `backend/.venv`**. No instales paquetes globalmente ni cambies el Python del sistema.
- Fija versiones compatibles y reproducibles en `requirements.txt`.
- No dupliques dependencias ni actualices paquetes sin justificación.

### 4.2 Servicio PostgreSQL local de pruebas

Comprueba si existe PostgreSQL local, `pg_isready`, Docker o Podman.

- Si PostgreSQL ya está instalado y configurado, utiliza una base de datos de pruebas desechable y credenciales locales temporales.
- Si Docker/Podman está disponible, puedes usar un contenedor PostgreSQL temporal y aislado, enlazado únicamente a `127.0.0.1`, con credenciales desechables. No reutilices volúmenes ni contenedores existentes que no hayas creado tú.
- Si es necesario instalar PostgreSQL, Docker, iniciar servicios del sistema con `sudo`, cambiar firewall o instalar infraestructura, detente en esa operación y solicita autorización concreta. Continúa mientras tanto con las demás tareas.
- No descargues ni expongas secretos reales.
- No conectes ni migres una base de datos de producción.

### 4.3 Validación efectiva

Cuando PostgreSQL esté disponible:
- Configura variables de entorno temporales para tests.
- Ejecuta migraciones sobre una base de pruebas vacía.
- Ejecuta la suite completa sobre PostgreSQL.
- Ejecuta pruebas de integridad, aislamiento y concurrencia.
- Comprueba transferencia de propiedad y cambios de membresía concurrentes.
- Comprueba constraints, rollback y errores esperados.
- Registra versiones de PostgreSQL y del driver.

No afirmes que PostgreSQL está validado si no se ejecutaron las pruebas sobre ese motor.

### 4.4 SQLite local

Las migraciones `cuentas.0001_initial` y `inteligencia_artificial.0003`–`0006` aparecían pendientes en la SQLite persistente.

Antes de aplicar migraciones a la base SQLite local:
1. Identifica el archivo de base de datos real en settings.
2. Crea una copia consistente de seguridad fuera del repositorio, usando el mecanismo de backup de SQLite.
3. Verifica que el backup se haya creado y tenga tamaño razonable.
4. Solo entonces aplica las migraciones al entorno local de desarrollo.
5. Comprueba `showmigrations` y realiza una prueba breve de lectura.
6. No elimines el backup automáticamente.

No ejecutes nunca migraciones sobre una base de datos real de producción.

---

## 5. OPENAPI — GENERACIÓN Y CONTRATO REAL

La ruta `/api/schema/` ya se había configurado, pero no pudo verificarse.

- Inspecciona el backend de esquemas actual y las versiones instaladas.
- Instala dentro del venv las dependencias fijadas que realmente requiera la implementación (`uritemplate`, `inflection` u otras, solo si son necesarias).
- Si el generador actual no es compatible con el proyecto, reemplázalo por una solución mantenida y compatible, con cambios mínimos y justificados.
- Asegura que el esquema se genere sin errores.
- Comprueba que incluya todos los endpoints, métodos, request/response, JWT, `X-Workspace-ID`, roles, paginación, errores, consentimiento IA y operaciones de cuentas.
- Corrige las advertencias relevantes de documentación.
- Añade pruebas que soliciten el esquema y comprueben que devuelve un documento válido y contiene rutas clave.
- Documenta cómo abrir o exportar el esquema.

No declares OpenAPI terminado hasta generar y validar el esquema real.

---

## 6. CUENTAS, REGISTRO, PERFIL Y CORREO

La decisión confirmada es que habrá registro público y creación administrativa.

Audita la app `cuentas` existente y completa los flujos:

- Registro público.
- Creación administrativa.
- Creación transaccional de usuario, perfil, workspace personal y membresía OWNER.
- Perfil autenticado.
- Cambio de contraseña.
- Solicitud de recuperación.
- Confirmación de recuperación.
- Verificación de correo.
- Reenvío de verificación.
- Bloqueo de usuarios inactivos.
- Throttling adecuado.
- Respuestas de recuperación que no permitan enumerar cuentas.
- Validaciones de contraseña y username.
- Revocación o invalidación adecuada de tokens después de cambio/restablecimiento de contraseña.

El modelo de usuario conocido es `django.contrib.auth.models.User`, `username` único y `email` no único. No conviertas email en identificador único ni cambies el modelo sin una necesidad demostrada y un plan de migración.

### Correo

- Mantén backend de consola/locmem para desarrollo y tests.
- Configura SMTP mediante variables de entorno en producción.
- No inventes credenciales.
- Prueba todos los flujos usando `locmem` y mocks.
- Si las credenciales SMTP reales ya están configuradas, no las imprimas. No envíes correos a terceros ni mensajes reales sin autorización del usuario.
- Si no hay SMTP disponible, documenta la dependencia externa como pendiente de verificación real.
- Comprueba que los enlaces sean válidos y correspondan a rutas reales del frontend o a una URL configurable. No generes enlaces que apunten a endpoints POST no utilizables como navegación normal sin explicar el flujo.
- No afirmes que el correo real funciona basándote solamente en mocks.

---

## 7. SEGURIDAD, MULTI-TENANCY Y WORKSPACES

Revalida y corrige si fuera necesario:

- JWT y autenticación.
- `WorkspaceContextMixin`.
- RBAC OWNER, ADMIN, EDITOR y VIEWER.
- Filtrado de querysets por workspace.
- Vistas de detalle por ID.
- Acciones personalizadas.
- Ejecuciones, resultados y análisis IA.
- Administración de miembros.
- Transferencia de propiedad.
- Django Admin.
- Coherencia `Workspace.propietario` / membresía OWNER.
- Coherencia de consumos entre producto y recurso.

Las transferencias deben dejar un único OWNER y sincronizar ambas representaciones dentro de una transacción. El anterior OWNER pasa a ADMIN; el destinatario debe ser miembro existente y activo.

Comprueba las restricciones ADMIN: no puede alterar OWNER ni otros ADMIN ni asignar ADMIN.

No permitas que el usuario envíe un workspace ID en el body para obtener acceso. Usa el workspace validado desde la URL/header y la membresía del usuario.

Añade pruebas que verifiquen el estado final de la base de datos, no solamente el código HTTP.

Revisa los accesos globales desde Django Admin a datos tenant-scoped. Si solo operadores globales de confianza deben usar el admin, deja claro y probado ese límite; si hay accesos de staff de distintos tenants, aísla sus querysets y permisos.

---

## 8. CONSENTIMIENTO DE IA Y GROQ

El consentimiento explícito es obligatorio antes de enviar información a Groq.

Verifica que:
- La comprobación se realice en backend.
- Una solicitud sin consentimiento no invoque al proveedor.
- El usuario pueda usar optimización sin IA.
- Se transmita únicamente el contexto mínimo.
- No se envíen identificadores, nombres, contraseñas, tokens o secretos innecesarios.
- La pregunta libre no se trate como dato seguro: valida y advierte que no debe incluir secretos o datos personales.
- Haya versión de aviso y evidencia de consentimiento suficiente.
- La idempotencia impida generar llamadas duplicadas.
- Existan estados y recuperación operativa para solicitudes que queden `PROCESSING` si el proceso cae.
- Timeout, errores, respuestas inválidas y límites se manejen con seguridad.
- Los errores internos no se expongan en mensajes públicos.

Pruebas:
- Sin consentimiento: respuesta esperada y cero llamadas al proveedor.
- Con consentimiento: proveedor mock invocado una vez.
- Idempotency-Key repetida: reutiliza resultado sin duplicar la llamada.
- Fallo del proveedor: no deja datos inconsistentes.
- Contexto: comprobar que no contiene datos sensibles innecesarios.

No realices llamadas reales ni pagadas a Groq en la suite rutinaria. Si hay una API key local, no la imprimas ni uses el servicio real sin autorización específica.

La documentación informativa no sustituye revisión legal de política de privacidad. Señala esa limitación.

---

## 9. OPTIMIZACIÓN MATEMÁTICA Y SOLVER

Audita el solver CBC y completa las pruebas para:
- Maximización.
- Datos incompletos o inválidos.
- Soluciones óptimas.
- Problemas inviables.
- Problemas no acotados.
- Estados no resueltos.
- Errores del solver.
- Límites de tiempo.
- Límites de productos y recursos.
- Persistencia y consistencia de resultados.
- Casos límite.

Separa errores internos de mensajes públicos. No devuelvas `str(exception)` al usuario si revela detalles internos.

### Minimización sigue siendo una decisión bloqueada

El usuario no ha definido qué significa minimizar en PlanificaIO. El informe previo detectó que minimizar la suma de utilidades no negativas produce la solución trivial de cero cuando no hay producción mínima.

**No inventes costos, demanda, producción mínima ni cambies la función objetivo.**

No implementes ni declares soportada una semántica nueva de minimización. Mantén el comportamiento existente documentado y presenta al usuario, en el informe final, estas alternativas:
1. Minimizar costos (requiere campos/valores de costo).
2. Minimizar consumo de recursos sujeto a producción mínima.
3. Ofrecer únicamente maximización y retirar minimización del contrato funcional.
4. Otra función objetivo definida por el usuario.

Completa todo lo demás. Esta decisión debe quedar como el único bloqueo matemático y no debe impedir cerrar pruebas de maximización y estados del solver.

---

## 10. ERRORES, PAGINACIÓN, LÍMITES Y RENDIMIENTO

Audita y completa:

- Paginación coherente en endpoints de colección.
- Compatibilidad de pruebas existentes con respuestas paginadas.
- Límites de `page_size`.
- Límites de productos/recursos por problema.
- Límite de tiempo del solver.
- Timeout del proveedor Groq.
- Throttling.
- Respuestas de error uniforme.
- Separación entre detalle público y diagnóstico interno.
- Logging estructurado sin secretos ni payloads sensibles.
- Optimización N+1 con `select_related`/`prefetch_related`.
- Índices para filtros usados.
- Consultas repetidas.
- Protección contra cargas excesivas.

No agregues Redis, Celery u otros servicios por moda. Si el despliegue tendrá varios workers, el throttling debe usar un backend de caché compartido; evalúa caché de base de datos PostgreSQL o Redis y documenta la elección. Si falta infraestructura externa, configura una opción reproducible y marca lo no probado.

Para trabajos largos, decide si basta con límites síncronos o se necesita cola. No incorpores una cola si no hay evidencia de necesidad y posibilidad de probarla.

---

## 11. PREPARACIÓN Y VALIDACIÓN DE PRODUCCIÓN

Completa la configuración por entorno y valida:

- `DEBUG=False`.
- `SECRET_KEY` obligatoria, fuerte y nunca impresa.
- `ALLOWED_HOSTS` explícito.
- `DATABASE_ENGINE=postgresql` para producción.
- Credenciales de PostgreSQL por entorno.
- HTTPS y configuración segura de cookies.
- HSTS configurado con criterio.
- CORS restringido a orígenes configurados; no wildcard indiscriminado.
- CSRF coherente con frontend y autenticación.
- SMTP por entorno.
- Groq por secreto.
- Logging.
- Static files.
- Servidor WSGI/ASGI.
- Health check que no filtre información.
- Dependencias fijadas.
- Guía reproducible de instalación y despliegue.
- Backup y restore documentados y probados en base desechable.

Ejecuta `python manage.py check --deploy` con configuración de producción de prueba. Corrige los warnings que puedas corregir sin inventar dominios, certificados o secretos. Los valores que dependan del despliegue real deben estar documentados como variables obligatorias.

No despliegues públicamente ni crees infraestructura en la nube.

### Backup y restore

Implementa y documenta el procedimiento adecuado para PostgreSQL. Prueba backup/restore únicamente sobre una base desechable, con datos sintéticos. Verifica conteos e integridad después de restaurar. Nunca sobrescribas la base local del usuario ni una base real.

---

## 12. VALIDACIÓN FINAL OBLIGATORIA

Ejecuta pruebas focalizadas para cada área y después la suite completa.

Desde `backend/`:

```bash
.venv/bin/python -m compileall -q apps config
.venv/bin/python manage.py test -v 2
.venv/bin/python manage.py check
.venv/bin/python manage.py makemigrations --check --dry-run
.venv/bin/python manage.py showmigrations
.venv/bin/python manage.py check --deploy
```

Ejecuta además:
- Suite completa en SQLite para compatibilidad de desarrollo.
- Suite completa en PostgreSQL si el servicio está disponible.
- Pruebas reales de generación OpenAPI.
- Pruebas de registro, email, recuperación y cuenta con backend de correo de prueba.
- Pruebas de consentimiento IA con mocks.
- Pruebas de concurrencia sobre PostgreSQL.
- Prueba de backup/restore en base desechable.
- `git diff --check`.
- Verificación de que no hay secretos incorporados al repositorio.
- Verificación final `git status -sb`.

No modifiques las expectativas de tests solo para obtener verde. Corrige el código o explica con evidencia por qué una prueba está equivocada.

No afirmes que una prueba pasó si no se ejecutó. No afirmes que un servicio real funciona porque se simuló.

---

## 13. CONDICIONES DE BLOQUEO Y AUTORIZACIONES

Puedes instalar dependencias Python declaradas dentro de `backend/.venv`.

No instales paquetes globales ni utilices `sudo` sin autorización explícita. No instales servicios del sistema, Docker o PostgreSQL sin solicitar la autorización concreta necesaria. Puedes usar un PostgreSQL local o un contenedor temporal si ya existe infraestructura Docker/Podman disponible.

No uses credenciales reales sin que estén configuradas por el usuario. No imprimas `.env`, tokens, contraseñas ni claves.

No envíes emails reales ni hagas llamadas pagadas a Groq sin autorización.

Si un servicio externo no está disponible:
- Completa la configuración y las pruebas simuladas.
- Documenta el comando exacto que falta.
- Explica qué prueba real no pudo ejecutarse.
- Continúa con todas las demás tareas.

No bloquees todo el trabajo por una dependencia externa.

---

## 14. QUÉ SIGNIFICA TERMINAR

No uses un porcentaje subjetivo para afirmar que el backend está al 100 %.

Considera el backend técnicamente listo para integración frontend cuando:
- Las funcionalidades definidas están implementadas.
- Los endpoints y contratos son estables y documentados.
- JWT, cuentas, RBAC y aislamiento están probados.
- Las operaciones compuestas conservan integridad.
- PostgreSQL ha sido validado en pruebas, o el bloqueo está expresamente identificado.
- El solver está validado para las funciones objetivo acordadas.
- IA exige consentimiento en backend.
- Errores, límites y paginación tienen comportamiento definido.
- OpenAPI se genera y refleja la API real.
- Configuración de producción pasa las comprobaciones posibles.
- Los procedimientos de instalación, migración y recuperación son reproducibles.
- No existen fallos de pruebas conocidos sin explicación.

La minimización no puede darse por terminada hasta que el usuario elija su significado. No ocultes ese bloqueo.

La preparación de producción puede estar completa a nivel de configuración y validación técnica sin desplegar públicamente, pero distingue claramente entre “preparado”, “probado en entorno de ensayo” y “desplegado y verificado”.

---

## 15. INFORME FINAL Y ENTREGA

Cuando hayas completado todas las tareas posibles, detente y entrega un informe en el chat con:

1. Resumen ejecutivo.
2. Matriz por área: implementado y verificado, parcial, no implementado o no verificable.
3. Funcionalidades añadidas y corregidas.
4. Archivos creados, modificados y eliminados.
5. Migraciones creadas y cuáles se aplicaron a cada base.
6. Endpoints nuevos o modificados.
7. Resultados de las pruebas, separados por SQLite y PostgreSQL.
8. Resultado de compileall, `check`, `check --deploy`, migraciones, OpenAPI y `git diff --check`.
9. Resultado de registro, email, consentimiento IA y backup/restore.
10. Problemas encontrados y corregidos.
11. Riesgos y bloqueos pendientes.
12. Decisión exacta que falta sobre minimización, con ejemplos matemáticos.
13. Dependencias/credenciales/servicios externos que requieren intervención del usuario.
14. Criterios que se cumplen y los que no.
15. Porcentaje solo si explicas la metodología; es preferible no inventarlo.
16. Secuencia propuesta de commits pequeños, agrupados por funcionalidad.
17. Estado Git final y confirmación de que no se publicó nada.

No digas “backend 100 % terminado” si PostgreSQL, OpenAPI, correo, backup/restore o cualquier otro criterio crítico no pudo verificarse.

Al terminar el informe, espera mi revisión. No hagas commit, push ni publiques nada.

---

## INSTRUCCIÓN FINAL

Trabaja ahora directamente en el repositorio local. Completa todo lo que esté definido, seguro y disponible. Prioriza las pruebas reales y la integridad del sistema sobre la cantidad de código.

Quiero terminar hoy el máximo trabajo posible y dejar el backend listo para pasar al frontend React. No inventes resultados para alcanzar esa fecha.

**Tu autonomía termina en los cambios locales, pruebas y documentación. La aceptación final, los commits y toda publicación en GitHub corresponden exclusivamente al usuario.**
