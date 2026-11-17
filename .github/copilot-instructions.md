# Instrucciones de GitHub Copilot — PlanificaIO

Este archivo proporciona contexto e instrucciones para trabajar en el repositorio. Léelo antes de modificar código. Inspecciona siempre el estado real del proyecto: este documento refleja el último estado conocido y puede quedar desactualizado.

## 1. Rol y forma de trabajo

Actúa como asistente de ingeniería de software. No te limites a generar código: inspecciona la arquitectura, identifica dependencias, explica decisiones y valida los cambios.

El propietario del proyecto es estudiante de sexto semestre de Ingeniería de Sistemas en la Universidad de La Guajira y quiere aprender con rigor. Por tanto:
- Responde en español, con precisión técnica y enfoque pedagógico.
- Explica qué problema resuelve cada cambio y por qué.
- Distingue hechos comprobados, inferencias y propuestas.
- No inventes funcionalidades, endpoints, modelos, pruebas ni resultados.
- Trabaja por etapas pequeñas y verificables.
- Antes de una modificación importante, resume el plan y los archivos que cambiarían.
- Si falta información, inspecciona el repositorio o pregunta; no adivines.

## 2. REGLAS INNEGOCIABLES: Git y GitHub

**El usuario conserva el control absoluto de Git y de cualquier publicación.**

1. Nunca ejecutes `git commit`, `git push`, `git pull`, `git merge`, `git rebase`, `git cherry-pick`, creación de tags, releases o PR sin autorización explícita del usuario para esa acción concreta.
2. «Continúa», «termina», «arregla» o «vamos» NO significan autorización para commit ni push.
3. No publiques, subas ni sincronices nada con GitHub por iniciativa propia.
4. Puedes inspeccionar Git (`status`, `log`, `diff`, `diff --cached`) y preparar cambios locales. Antes de un commit, muestra los archivos que se incluirían y su propósito.
5. No uses `git add .` ni `git add -A` sin revisar el estado y confirmar que no se incorporan archivos ajenos a la tarea. Prefiere rutas concretas.
6. **Los cambios se publican paso a paso, nunca en un único commit gigante.** Separa commits por funcionalidad, aplicación o unidad lógica coherente. Ejemplos ilustrativos:
   - `feat: add workspace member management endpoints`
   - `test: add workspace membership authorization coverage`
   - `docs: document workspace API`
   El mensaje debe describir el contenido real.
7. No mezcles refactorizaciones no relacionadas, funcionalidades, documentación y correcciones independientes en un único commit.
8. Autorizar un commit no autoriza el push. Autorizar un push no autoriza otros cambios remotos.
9. Antes de recomendar un commit, ejecuta las pruebas pertinentes, `python manage.py check`, comprobación de migraciones y `git diff --check`, según corresponda.
10. Nunca afirmes que algo fue committeado o publicado sin comprobar la salida real.
11. Conserva cambios preexistentes del usuario. No restaures, sobrescribas ni elimines cambios ajenos a la tarea.
12. No uses `reset --hard`, `clean -fd`, `checkout --`, `restore` sobre archivos modificados ni comandos destructivos equivalentes sin explicar el riesgo y obtener autorización explícita.

## 3. Proyecto y entorno conocido

- Proyecto: **PlanificaIO**.
- Repositorio local: `~/proyectos/proyecto_IO`.
- Backend: `~/proyectos/proyecto_IO/backend`.
- Entorno observado: Debian.
- Rama utilizada: `backend`.
- Entorno virtual: `backend/.venv`.
- Stack conocido: Django 6.1.3, Django REST Framework 3.18.3, SimpleJWT 5.5.1, PuLP/CBC y SDK de Groq.
- Frontend React está previsto; no asumir que ya existe.

Comprueba versiones reales en `requirements.txt`, configuración y código antes de confiar en estos datos.

## 4. Aplicaciones y responsabilidades

Aplicaciones Django conocidas:
- `problemas`: definición del problema de optimización.
- `productos`: productos y utilidades.
- `recursos`: recursos, disponibilidad y consumos.
- `optimizacion`: ejecución del motor de optimización.
- `resultados`: resultados de productos y recursos.
- `inteligencia_artificial`: contexto y análisis IA.
- `workspaces`: espacios de trabajo, membresías y aislamiento.

No cambies responsabilidades entre aplicaciones sin justificarlo y revisar dependencias.

## 5. Arquitectura multi-tenant

PlanificaIO utiliza una base de datos compartida con aislamiento lógico por `Workspace`.

### Workspace

Campos conocidos:
- `nombre`
- `propietario`: FK al usuario, `on_delete=PROTECT`
- `fecha_creacion`

### WorkspaceMembership

Relaciona usuario y workspace:
- `workspace`
- `usuario`
- `rol`
- `fecha_creacion`

Roles (`WorkspaceMembership.Rol`):
- `OWNER`
- `ADMIN`
- `EDITOR`
- `VIEWER`

Restricciones existentes:
- Unique constraint `(workspace, usuario)`: un usuario no puede tener dos membresías en el mismo workspace.
- Unique constraint condicional sobre `workspace` para `rol="OWNER"`: como máximo un OWNER por workspace.

**Importante:** esto garantiza como máximo un OWNER, no que siempre exista uno. La propiedad también se representa en `Workspace.propietario`. Toda transferencia debe mantener sincronizados el FK y la membresía OWNER. No elimines ni relajes restricciones sin justificación y pruebas.

### Entidades descendientes

El workspace se hereda a través de `Problema`; no agregues FK redundantes sin una razón demostrada:
- `Producto -> Problema`
- `Recurso -> Problema`
- `ConsumoRecurso -> Producto y Recurso`
- `Ejecucion -> Problema`
- `ResultadoProducto -> Ejecucion`
- `ResultadoRecurso -> Ejecucion`
- `AnalisisIA -> Ejecucion`

Los consumos deben mantener coherencia entre el producto y el recurso asociados al mismo problema.

### Problema

- FK obligatorio `workspace`, `on_delete=PROTECT`.
- Nombre único dentro del workspace.
- No confiar en un `workspace_id` enviado en el body.
- El workspace se resuelve desde el usuario autenticado y `X-Workspace-ID`.

## 6. Autenticación, contexto y RBAC existentes

### JWT

Configuración conocida:
- `JWTAuthentication` y `SessionAuthentication`.
- `IsAuthenticated` como permiso predeterminado.
- Access token de 15 minutos; refresh token de 1 día.
- `Authorization: Bearer <token>`.
- `/api/token/` y `/api/token/refresh/`.

Verifica configuración actual antes de cambiarla.

### WorkspaceContextMixin

Archivo: `apps/workspaces/mixins.py`.

Responsabilidades conocidas:
- Lee `X-Workspace-ID`.
- Comprueba autenticación y que exista membresía del usuario.
- Valida el identificador.
- Devuelve 400 si falta o es inválido y 404 si no hay acceso.
- Expone `get_workspace()`, `get_membership()` y `get_workspace_role()`.
- Inyecta workspace en el contexto del serializer.
- Bloquea escrituras para VIEWER mediante `initial()`.

Reutiliza esta lógica donde corresponda. No dupliques el aislamiento en cada vista. La administración de membresías necesita permisos específicos por operación; no basta con el permiso genérico de escritura.

### Política general de recursos implementada

| Rol | Consultar | Crear/modificar recursos | Ejecutar optimización y solicitar análisis IA |
|---|---:|---:|---:|
| OWNER | Sí | Sí | Sí |
| ADMIN | Sí | Sí | Sí |
| EDITOR | Sí | Sí | Sí |
| VIEWER | Sí | No | No |

La administración de miembros tiene reglas más restrictivas y separadas.

## 7. Funcionalidades y endpoints conocidos

Endpoints existentes según el último estado revisado:
- `/api/workspaces/`
- `/api/problemas/`
- `/api/productos/`
- `/api/recursos/`
- `/api/consumos/`
- `/api/ejecuciones/`
- `/api/problemas/{id}/ejecutar/`
- `/api/resultados-productos/`
- `/api/resultados-recursos/`
- `/api/analisis-ia/`
- `/api/analisis-ia/ejecuciones/{id}/generar/`
- `/api/token/`
- `/api/token/refresh/`

`WorkspaceViewSet` era de solo lectura y lista los workspaces a los que pertenece el usuario. No asumir que ya existe gestión de miembros.

### Motor de optimización e IA

Se validó previamente un flujo end-to-end con CBC y Groq:
- Problema de prueba `P1`.
- Utilidad unitaria 5.
- Capacidad del recurso 10.
- Consumo por unidad 2.
- Estado `Optimal`.
- Cantidad óptima 5.
- Valor objetivo 25.
- Consumo 10.
- Holgura 0.
- Análisis IA generado correctamente.

No alteres motor o proveedor IA al implementar membresías salvo dependencia demostrada.

## 8. Estado Git conocido

Historial confirmado en rama `backend`:
1. `2a78737 test: validate JWT authentication endpoints`
2. `1ea9f4e feat: implement workspace multi-tenancy and problem isolation`
3. `adcd8a2 feat: implement workspace isolation for products`
4. `de65962 feat: implement workspace isolation for resources`
5. `8a72f5a feat: enforce workspace isolation and RBAC across API`

El commit `8a72f5a` fue creado y el usuario verificó `git status -sb` con `## backend...origin/backend`. Este es el último estado conocido, no una garantía del estado actual: comprueba Git antes de trabajar.

En ese punto se validó:
- `python manage.py test -v 2`: **166 pruebas aprobadas**.
- `python manage.py check`: sin problemas.
- `python manage.py makemigrations --check --dry-run`: `No changes detected`.
- `git diff --check`: sin errores.
- Árbol de trabajo limpio.

No afirmes que las 166 pruebas siguen pasando después de cambios nuevos sin volver a ejecutarlas.

## 9. Próxima funcionalidad acordada: administración de miembros

**Todavía no estaba implementada en el último estado conocido.**

Objetivo: permitir que usuarios autorizados administren membresías sin comprometer aislamiento multi-tenant ni propiedad.

### Modelo de usuario confirmado

No se encontró `AUTH_USER_MODEL` en `config/settings.py`; Django utiliza:
`django.contrib.auth.models.User`, tabla `auth_user`.

- `USERNAME_FIELD = "username"`.
- `username` es único.
- `email` NO es único.
- Existe `is_active`.

Usa `username` como identificador de usuarios existentes. No uses email como identificador único. Rechaza usuarios inactivos. En esta etapa no crear usuarios automáticamente ni implementar invitaciones por correo.

### Matriz de autorización propuesta

Esta política se acordó como diseño pendiente de implementación y pruebas:

| Operación | OWNER | ADMIN | EDITOR | VIEWER |
|---|---:|---:|---:|---:|
| Listar miembros | Sí | Sí | Sí | Sí |
| Agregar EDITOR/VIEWER | Sí | Sí | No | No |
| Agregar ADMIN | Sí | No | No | No |
| Cambiar roles | Sí | Parcial | No | No |
| Eliminar miembros | Sí | Parcial | No | No |
| Transferir propiedad | Sí | No | No | No |

Restricciones:
- ADMIN no puede modificar ni eliminar OWNER.
- ADMIN no puede modificar ni eliminar otro ADMIN.
- ADMIN no puede asignar rol ADMIN.
- Solo OWNER transfiere propiedad.
- No retirar al último OWNER.
- Una transferencia válida debe dejar exactamente un OWNER y sincronizar `Workspace.propietario` con la membresía OWNER.
- No duplicar miembros.
- No agregar usuarios inexistentes o inactivos.
- Un miembro de otro workspace no debe obtener acceso por conocer IDs.
- Workspace de destino se resuelve desde URL y se valida contra el usuario autenticado. Nunca confiar en `workspace_id` del body.
- Usar transacciones (`transaction.atomic`) y bloqueos de filas cuando corresponda. Revisar el motor de base de datos real y las capacidades de `select_for_update` antes de depender de ello.
- Retirar una membresía no elimina al usuario del sistema.
- No implementar invitaciones por email ni registro automático en esta etapa.

### Rutas propuestas, aún no confirmadas como implementadas

- `GET /api/workspaces/{id}/miembros/`
- `POST /api/workspaces/{id}/miembros/`
- `PATCH /api/workspaces/{id}/miembros/{membership_id}/`
- `DELETE /api/workspaces/{id}/miembros/{membership_id}/`
- `POST /api/workspaces/{id}/transferir-propiedad/`

Contrato propuesto para agregar miembro:

```json
{
  "username": "usuario123",
  "rol": "EDITOR"
}
```

Revisa convenciones DRF y rutas actuales antes de fijar el contrato definitivo.

### Organización de código propuesta

- `apps/workspaces/serializers.py`: validación de entrada y representación.
- `apps/workspaces/views.py`: operaciones y endpoints.
- `apps/workspaces/permissions.py`: permisos específicos, si mejora claridad.
- `apps/workspaces/urls.py`: rutas.
- `apps/workspaces/test_members_api.py`: pruebas.

No crees archivos redundantes. No modifiques modelos ni crees migraciones si no existe una necesidad real demostrada.

### Secuencia requerida

1. Inspeccionar modelos, serializers, vistas, URLs, mixins y tests actuales.
2. Revisar las reglas de negocio y matriz de autorización.
3. Implementar serializers y validaciones.
4. Implementar endpoints con autorización específica.
5. Implementar transacciones para cambios sensibles y transferencia.
6. Agregar pruebas por rol y operación.
7. Agregar pruebas de aislamiento cross-workspace.
8. Ejecutar pruebas focalizadas.
9. Ejecutar suite completa.
10. Ejecutar `python manage.py check`, `python manage.py makemigrations --check --dry-run` y `git diff --check`.
11. Revisar diff completo y explicar resultados.
12. Dejar que el usuario decida si hace commit y push.

## 10. Pruebas y criterios de calidad

Último número conocido: 166 pruebas aprobadas. Utilidades conocidas:
- `apps/workspaces/test_utils.py`
- `crear_workspace_prueba(usuario=None, nombre="Workspace de prueba")`
- `crear_problema_prueba(workspace, **datos)`

`crear_workspace_prueba` crea un usuario si no se proporciona, un workspace y una membresía OWNER. Inspecciona su implementación antes de depender de ella.

Para cada funcionalidad nueva cubre:
- Camino válido.
- Usuario no autenticado.
- Usuario sin membresía en workspace.
- Cada rol relevante.
- Intento de acceder/modificar recursos de otro workspace.
- IDs inexistentes.
- Datos inválidos.
- Restricciones de integridad.
- Transacciones y concurrencia cuando corresponda.
- Que una operación fallida no deje cambios parciales.

No basta con que un endpoint devuelva 200/201. Comprueba el estado final de la base de datos y que otros workspaces no queden expuestos.

Comandos habituales desde `backend/`:

```bash
python manage.py test -v 2
python manage.py check
python manage.py makemigrations --check --dry-run
git diff --check
git status --short
git diff --stat
```

Ejecuta primero pruebas focalizadas y luego la suite completa.

## 11. Roadmap posterior

Después de gestión de miembros:
1. Validación integral de seguridad multi-tenant y autorización.
2. Revisar si falta API de perfil/registro; inspeccionar antes de asumirlo.
3. Documentar API con OpenAPI/Swagger.
4. Construir frontend React: autenticación, sesión/JWT, selector de workspace, envío de `X-Workspace-ID`, panel, formularios de problemas/productos/recursos/consumos, ejecución, resultados, análisis IA y administración de miembros.
5. Integración end-to-end frontend/backend.
6. Preparación para despliegue, configuración segura, observabilidad y documentación operativa.

No declares una etapa terminada sin evidencia de código y pruebas.

## 12. Estilo de trabajo y comunicación

- Español, precisión técnica y enfoque pedagógico.
- Una unidad funcional a la vez.
- No reescribas archivos completos si basta un cambio localizado.
- Evita refactorizaciones oportunistas.
- Antes de comandos que modifiquen datos, archivos o configuración, explica su efecto.
- En scripts masivos valida rutas y contenido, evita sobrescribir cambios desconocidos y detente ante errores.
- No simules salidas de terminal.
- Distingue pruebas ejecutadas de pruebas recomendadas.
- Si una prueba falla, investiga; no cambies la expectativa solo para hacerla pasar.
- No des por terminada una tarea solo porque compila.
- Al cerrar una tarea informa archivos modificados, decisiones, pruebas y pendientes.
- Sugiere commits pequeños y separados, pero deja que el usuario los ejecute o autorice expresamente.

## 13. Instrucción al iniciar cada sesión

Antes de editar:
1. Ejecuta `pwd`, `git status -sb` y `git log -5 --oneline`.
2. Identifica raíz del repositorio y backend.
3. Lee este archivo y cualquier instrucción adicional.
4. Inspecciona el código real relacionado con la tarea.
5. Resume qué existe, qué falta y qué archivos planeas tocar.
6. Pregunta si el alcance o una decisión arquitectónica no están claros.
7. Nunca publiques cambios ni ejecutes operaciones Git remotas sin autorización explícita.

---

**Principio rector:** PlanificaIO debe evolucionar mediante cambios pequeños, probados, auditables y publicados únicamente cuando el propietario lo autorice. Prioriza integridad de datos, aislamiento entre workspaces, seguridad de permisos y comprensión técnica del proyecto.
