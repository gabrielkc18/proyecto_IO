# Operación del backend de PlanificaIO

Este documento describe cómo instalar y operar el backend actual. No constituye una política de privacidad ni evidencia de que se haya desplegado o probado en producción.

## Requisitos y configuración local

El backend requiere las versiones fijadas en [`backend/requirements.txt`](../backend/requirements.txt). Para desarrollo con SQLite:

```bash
cd backend
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

Reemplaza `SECRET_KEY` por un valor aleatorio privado. No incluyas `.env`, claves de Groq, contraseñas de base de datos ni credenciales de correo en Git. Después:

```bash
.venv/bin/python manage.py migrate
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py runserver
```

El backend lee su configuración desde variables de entorno y `.env` mediante `python-decouple`. `.env.example` contiene solo valores de muestra. En desarrollo, el correo se imprime en consola por defecto.

## PostgreSQL

PostgreSQL es el motor objetivo de producción. Define `DATABASE_ENGINE=postgresql`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST` y `POSTGRES_PORT`. `POSTGRES_CONN_MAX_AGE` y `POSTGRES_CONNECT_TIMEOUT` controlan la duración y el tiempo máximo de conexión.

No uses una base con datos reales para validar cambios. En una instancia local o efímera:

```bash
cd backend
.venv/bin/python manage.py migrate
.venv/bin/python manage.py test -v 2
.venv/bin/python manage.py check
.venv/bin/python manage.py makemigrations --check --dry-run
```

El entorno de desarrollo puede usar SQLite. En producción, el backend rechaza SQLite y requiere `DJANGO_ENV=production`, `DEBUG=False` y `ALLOWED_HOSTS` explícito. La aplicación usa `select_for_update()` en cambios sensibles de membresías y en el aprovisionamiento de workspaces; esos bloqueos requieren validación en PostgreSQL, pues SQLite no ofrece el mismo bloqueo de filas.

## Variables de producción

Configura secretos y valores específicos del entorno fuera del repositorio:

- `DJANGO_ENV=production`, `DEBUG=False`, `SECRET_KEY` y `ALLOWED_HOSTS`.
- `DATABASE_ENGINE=postgresql` y las variables de conexión PostgreSQL.
- Un backend SMTP real mediante `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` o `EMAIL_USE_SSL`, `EMAIL_TIMEOUT` y `DEFAULT_FROM_EMAIL`.
- `ACCOUNT_EMAIL_VERIFICATION_URL` y `ACCOUNT_PASSWORD_RESET_URL` con rutas HTTPS del cliente que gestione los enlaces, si se usa una aplicación web separada.
- `GROQ_API_KEY` y `GROQ_MODEL` únicamente si se habilita el análisis de IA. La clave no debe registrarse ni quedar en el cliente.
- `OPTIMIZATION_TIME_LIMIT_SECONDS`, `OPTIMIZATION_MAX_PRODUCTS`, `OPTIMIZATION_MAX_RESOURCES` y `GROQ_TIMEOUT_SECONDS`, dentro de límites operativos razonables.
- `LOG_LEVEL` y `DJANGO_LOG_LEVEL` según el sistema de observabilidad del despliegue.

La configuración activa HTTPS redirect, cookies seguras y HSTS por defecto en producción. `SECURE_HSTS_PRELOAD` queda desactivado; `check --deploy` reportará W021 hasta que el propietario del dominio y del despliegue decida habilitar preload, que puede tener efectos duraderos en navegadores. No se configura CORS: se espera mismo origen o un proxy controlado. Si TLS termina en un proxy, su cabecera de protocolo debe configurarse y confiarse explícitamente antes de habilitar la aplicación detrás de él. No publiques el servicio directamente a Internet hasta validar la configuración de proxy, TLS, correo y PostgreSQL.

Secuencia orientativa de preparación de una instancia:

```bash
cd backend
.venv/bin/python manage.py check --deploy
.venv/bin/python manage.py migrate
.venv/bin/python manage.py createcachetable planificai_cache
.venv/bin/python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 60
```

En producción, DRF usa la caché compartida de base de datos PostgreSQL para que el throttling se aplique entre workers; crea `planificai_cache` antes de recibir tráfico. En desarrollo y tests se usa caché local en memoria. El servidor estático, TLS, proxy inverso, rotación de logs, monitoreo y secretos son responsabilidad del entorno de despliegue; no se crean infraestructura ni servicios externos desde este repositorio.

## Health check y diagnóstico

`GET /health/` ejecuta `SELECT 1` contra la base de datos y devuelve `{"status":"ok"}` o HTTP 503 con `{"status":"unavailable"}`. No comprueba Groq, el correo, CBC ni la salud completa del servicio. Los errores de base de datos se registran en el logger del servidor; la respuesta no incluye detalles internos.

Los errores del solver se registran en el servidor y la API devuelve un mensaje genérico en `mensaje_error`. Los errores de Groq se normalizan y no deben incluir claves, contenido de respuesta del proveedor o datos de contexto en los logs.

## Copias de seguridad y restauración PostgreSQL

Usa una identidad de base de datos de privilegios mínimos y un archivo `.pgpass` protegido (`chmod 600`) o un mecanismo de secretos equivalente. No pongas contraseñas en scripts versionados ni en argumentos guardados en el historial del shell.

Ejemplo de copia lógica:

```bash
pg_dump --format=custom --no-owner --file=planificai-backup.dump \
  "host=$POSTGRES_HOST port=$POSTGRES_PORT dbname=$POSTGRES_DB user=$POSTGRES_USER"
pg_restore --list planificai-backup.dump
```

Para verificar una restauración, crea una base **desechable y vacía** y restaura allí:

```bash
createdb --host="$POSTGRES_HOST" --port="$POSTGRES_PORT" \
  --username="$POSTGRES_USER" planificai_restore_check
pg_restore --host="$POSTGRES_HOST" --port="$POSTGRES_PORT" \
  --username="$POSTGRES_USER" --no-owner \
  --dbname=planificai_restore_check planificai-backup.dump
```

Después de restaurar, valida migraciones y datos en esa instancia. No apuntes este procedimiento a una base existente: una restauración sobre datos activos requiere un plan de recuperación aprobado, ventana de mantenimiento y respaldo previo. La existencia de estos pasos no significa que se hayan ejecutado ni que el respaldo esté verificado.

## API

La especificación OpenAPI está expuesta en `GET /api/schema/` y la interfaz interactiva Swagger UI en `GET /api/docs/`. Para exportar y validar el contrato desde `backend/`:

```bash
.venv/bin/python manage.py spectacular \
  --file /tmp/planificai-openapi.yaml \
  --validate
```

La generación utiliza `drf-spectacular` y PyYAML, fijados en `requirements.txt`. El esquema documenta también operaciones protegidas; que una ruta aparezca en Swagger no concede acceso a ella. La documentación generada no reemplaza las reglas de autorización descritas aquí.

### Autenticación y workspace

Los endpoints protegidos usan `Authorization: Bearer <access-token>`. Obtén y renueva tokens mediante `POST /api/token/` y `POST /api/token/refresh/`. El access token dura 15 minutos y el refresh token un día. Tras cambiar o restablecer la contraseña se revocan los tokens anteriores.

Los endpoints de recursos de workspace requieren `X-Workspace-ID` con un workspace al que el usuario pertenezca. El servidor resuelve el workspace desde la membresía autenticada; un valor enviado en el body no concede acceso. Los endpoints de miembros usan el ID de workspace de la ruta y validan de nuevo la membresía.

| Rol | Consultar | Escribir recursos / ejecutar / solicitar IA | Administrar miembros |
|---|---:|---:|---|
| OWNER | Sí | Sí | Completo; única transferencia de propiedad |
| ADMIN | Sí | Sí | Puede agregar EDITOR/VIEWER y administrar miembros no OWNER/ADMIN |
| EDITOR | Sí | Sí | Solo consultar |
| VIEWER | Sí | No | Solo consultar |

Solo usuarios activos pueden incorporarse o recibir propiedad. Retirar a un miembro no elimina su cuenta. ADMIN no puede modificar/eliminar OWNER ni otro ADMIN, ni asignar ADMIN. La transferencia demueve al propietario anterior a ADMIN y sincroniza la FK y membresía OWNER en una transacción.

### Django Admin

`/admin/` es una consola global de operadores de plataforma, no una interfaz tenant-aware. Los modelos tenant-scoped solo son visibles para cuentas activas con `is_superuser`; algunas entidades operativas son de solo lectura y la edición de membresías está deshabilitada. Un superusuario puede consultar datos de todos los workspaces por diseño, así que nunca asignes `is_superuser` a personal de un tenant. La prueba de permisos cubre la denegación a usuarios regulares e inactivos y el acceso de un operador activo.

### Rutas y métodos

`/api/problemas/`, `/api/productos/`, `/api/recursos/` y `/api/consumos/` son colecciones con `GET` y `POST`; los detalles `/{id}/` permiten `GET`, `PUT`, `PATCH` y `DELETE`, sujetos al rol. El problema se asocia al workspace activo, no a un `workspace` arbitrario del body.

| Método y ruta | Uso |
|---|---|
| `GET /api/workspaces/`, `GET /api/workspaces/{membership_id}/` | Membresías del usuario autenticado y workspace asociado |
| `GET, POST /api/workspaces/{workspace_id}/miembros/` | Listar o agregar miembro; alta `{ "username": "usuario123", "rol": "EDITOR" }` |
| `PATCH, DELETE /api/workspaces/{workspace_id}/miembros/{membership_id}/` | Cambiar rol o retirar membresía; PATCH `{ "rol": "VIEWER" }` |
| `POST /api/workspaces/{workspace_id}/transferir-propiedad/` | Transferir a miembro activo; `{ "username": "usuario123" }` |
| `POST /api/problemas/{id}/ejecutar/` | Ejecutar optimización de un problema |
| `GET /api/ejecuciones/`, `GET /api/ejecuciones/{id}/` | Consultar ejecuciones |
| `GET /api/resultados-productos/`, `GET /api/resultados-productos/{id}/` | Consultar resultados de productos |
| `GET /api/resultados-recursos/`, `GET /api/resultados-recursos/{id}/` | Consultar resultados de recursos |
| `GET /api/analisis-ia/`, `GET /api/analisis-ia/{id}/` | Consultar análisis |
| `POST /api/analisis-ia/ejecuciones/{ejecucion_id}/generar/` | Solicitar análisis IA, requiere consentimiento y `Idempotency-Key` |
| `POST /api/auth/registro/` | Registro público y creación transaccional de workspace personal |
| `GET /api/auth/perfil/` | Consultar perfil autenticado |
| `POST /api/auth/cambiar-contrasena/` | Cambiar contraseña autenticado |
| `GET, POST /api/auth/verificar-correo/` | Mostrar confirmación y verificar correo |
| `POST /api/auth/verificar-correo/reenviar/` | Reenviar verificación sin revelar datos de cuenta |
| `POST /api/auth/recuperar-contrasena/` | Solicitar recuperación; respuesta genérica |
| `GET, POST /api/auth/recuperar-contrasena/confirmar/` | Mostrar formulario y confirmar recuperación |
| `POST /api/token/`, `POST /api/token/refresh/` | Obtener o renovar JWT |
| `GET /health/` | Health check de base de datos |
| `GET /api/schema/` | Especificación OpenAPI |

Los filtros disponibles son `problema` en productos, recursos, consumos, ejecuciones, resultados y análisis; `producto` y `recurso` en consumos; y `ejecucion` en resultados y análisis.

Las listas DRF usan páginas de 50 elementos por defecto. `?page=N` selecciona la página y `?page_size=N` permite entre 1 y 100 elementos. La respuesta contiene `count`, `next`, `previous` y `results`. El listado de miembros es un endpoint específico y devuelve una lista sin paginación.

Errores comunes: 400 para datos inválidos o falta de contexto requerido, 401 para falta de autenticación/credenciales inválidas, 403 para rol insuficiente, 404 para recursos inexistentes o fuera del workspace activo, 409 para conflictos concurrentes/de integridad y 429 cuando se supera el throttling. Un error externo de Groq se devuelve como 502.

#### Payloads principales

Los serializers de los recursos aceptan estos campos al crear; `id` y los campos de resultados/ejecuciones son de solo lectura:

Problema (`POST /api/problemas/`):

```json
{"nombre":"Producción","descripcion":"","sentido_objetivo":"MAXIMIZAR","estado":"BORRADOR"}
```

Producto (`POST /api/productos/`):

```json
{"problema":1,"codigo":"P1","nombre":"Producto","descripcion":"","utilidad_unitaria":"5.00","activo":true}
```

Recurso (`POST /api/recursos/`):

```json
{"problema":1,"nombre":"Materia prima","unidad_medida":"kg","disponibilidad":"10.00","activo":true}
```

Consumo (`POST /api/consumos/`):

```json
{"producto":1,"recurso":1,"cantidad_por_unidad":"2.0000"}
```

`POST /api/problemas/{id}/ejecutar/` no requiere payload. `GET /api/ejecuciones/` y los endpoints de resultados son de consulta; sus serializers exponen los campos del recurso, incluyendo estado, fechas y valores calculados. No se permite crear o alterar ejecuciones/resultados mediante esos endpoints.

Para las rutas de cuenta, las solicitudes JSON son:

| Ruta | Payload |
|---|---|
| `POST /api/auth/registro/` | `{"username":"usuario123","email":"persona@example.test","password":"...","password_confirm":"..."}` |
| `POST /api/auth/cambiar-contrasena/` | `{"current_password":"...","new_password":"...","new_password_confirm":"..."}` |
| `POST /api/auth/verificar-correo/` | `{"uid":"...","token":"..."}` |
| `POST /api/auth/verificar-correo/reenviar/` | `{"username":"usuario123"}` |
| `POST /api/auth/recuperar-contrasena/` | `{"username":"usuario123"}` |
| `POST /api/auth/recuperar-contrasena/confirmar/` | `{"uid":"...","token":"...","new_password":"...","new_password_confirm":"..."}` |
| `POST /api/token/` | `{"username":"usuario123","password":"..."}` |
| `POST /api/token/refresh/` | `{"refresh":"<refresh-token>"}` |

La ruta de confirmación de recuperación también acepta `GET` para mostrar el formulario HTML que recibe `uid` y `token` como parámetros de consulta. La verificación de correo ofrece la misma forma HTML en su ruta. El perfil se obtiene con `GET /api/auth/perfil/`; responde con username, email, nombre, apellido y estado de verificación.

Como los enlaces de verificación y recuperación llevan tokens temporales en la URL, configura el proxy y el servidor web para no conservar esos parámetros en logs de acceso ni reenviar la URL completa como `Referer`.

### Consentimiento y privacidad de IA

Cada solicitud requiere `consentimiento_confirmado: true`; omitirlo o enviarlo como `false` produce HTTP 400 antes de invocar Groq. Ejemplo:

Encabezado HTTP: `Idempotency-Key: 6ba7b810-9dad-41d1-80b4-00c04fd430c8`

```json
{
  "pregunta": "¿Qué recurso presenta menor holgura?",
  "consentimiento_confirmado": true
}
```

La solicitud requiere `Idempotency-Key` con un UUID. Un reintento con la misma clave y los mismos datos devuelve el análisis existente (HTTP 200) sin volver a llamar a Groq. Reutilizar la clave con datos diferentes, o repetir un intento que sigue en curso/falló, devuelve HTTP 409; un reintento intencional después de un fallo debe usar una clave nueva. El SDK de Groq tiene reintentos automáticos desactivados.

La versión `ai-disclosure-v1` envía a Groq el sentido objetivo, estado del solver, utilidad total, valores unitarios/cantidades/utilidades aportadas de productos, disponibilidad/consumo/holgura/uso y unidad de medida de recursos, además de la pregunta escrita por el usuario. No se envían nombres, códigos, IDs, snapshots de entrada, nombres de usuario, correo, tokens ni contraseñas. El contexto minimizado también se conserva en el análisis interno para trazabilidad. Evita incluir datos personales o secretos en la pregunta.

El backend almacena cada aceptación con su fecha, versión de la declaración, ID del usuario autenticado, ID de ejecución y huella de la solicitud; no conserva la pregunta en el registro de intentos fallidos. Un análisis exitoso también expone su marca de consentimiento. No existe consentimiento persistente: debe confirmarse en cada solicitud. La declaración es una propuesta técnica, no una política de privacidad revisada ni una afirmación de validez legal. La interfaz cliente debe presentarla claramente antes de enviar la solicitud.

## Limitaciones operativas conocidas

- Los límites de frecuencia usan throttling de DRF y la caché PostgreSQL compartida en producción. Esa configuración y la creación de su tabla no se validaron contra PostgreSQL en este entorno.
- CBC y Groq se llaman sincrónicamente. Los límites reducen el tiempo/tamaño de la operación, pero no constituyen una cola de trabajos. Si el proceso cae tras reservar una solicitud IA, su estado puede permanecer `PROCESSING`. Tras confirmar que el worker original ya no está ejecutándose, inspecciona el umbral con `manage.py recover_stale_ai_requests --older-than-minutes 30 --dry-run` y, si corresponde, márcalas como fallidas con el mismo comando sin `--dry-run`. Esto no repite ni cancela llamadas externas; el usuario debe reintentar con una nueva `Idempotency-Key`. No ejecutes la recuperación mientras la solicitud original todavía pueda finalizar.
- PostgreSQL, concurrencia, OpenAPI generado, despliegue, backup y restore deben verificarse en entornos efímeros dedicados antes de producción.
- La minimización matemática del objetivo sigue pendiente de una decisión de negocio separada; no confundirla con la minimización del contexto enviado a Groq.

El solver actual construye para ambos sentidos el objetivo `sum(utilidad_unitaria[i] * cantidad[i])`, con cantidades enteras no negativas y restricciones de consumo `sum(consumo[r,i] * cantidad[i]) <= disponibilidad[r]`. Como la utilidad no es negativa y la producción cero satisface las restricciones, `MIN` puede devolver trivialmente cero. No se cambió ese comportamiento. Para definir minimización, el producto debe decidir si busca, por ejemplo, minimizar costos con demanda mínima (`min sum(costo[i] * cantidad[i])`, sujeto a `cantidad[i] >= demanda[i]`) o minimizar uso ponderado de recursos para una producción requerida (`min sum(peso[r] * consumo[r])`, sujeto a metas de producción). Estas alternativas requieren datos y restricciones de negocio nuevos; no son equivalentes.
