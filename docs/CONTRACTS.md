# CONTRACTS

## Propósito del documento
Este documento fija los contratos funcionales del sistema en su estado actual:
- contratos del **core MVP ya implementado**;
- contratos actuales de la **API local** y la **UI web local**.

No pretende diseñar todavía un backend enterprise ni una plataforma multiusuario. Define solo lo necesario para mantener límites claros entre interfaz web, API local, CLI, runtime, capa de datos, agente y adapters.

## Convenciones de lectura
- `campo`: obligatorio.
- `campo?`: opcional.
- Las colecciones pueden venir vacías cuando el contrato lo permita, pero no deben cambiar de significado entre ejecuciones equivalentes.
- Todo el documento asume:
  - local-first;
  - un solo agente real;
  - un solo dataset principal por run;
  - ruta manual local al dataset;
  - DuckDB local;
  - Ollama local;
  - API local sin auth en esta fase.

---

## 1. RunRequest

### Propósito
Representa la solicitud interna de ejecución que entra en el core para lanzar un run analítico.

### Campos
- `agent_id`
- `dataset_path`
- `user_prompt`
- `session_id?`

### Reglas mínimas
- Se refiere a un único dataset principal por run.
- `agent_id` debe resolverse en el `Agent Registry`.
- `dataset_path` debe apuntar a un archivo local.
- Formatos soportados: `csv`, `xlsx`, `parquet`.
- `user_prompt` no puede ser vacío.

### Encaje
Lo construyen CLI o API antes de invocar el caso de uso principal.

---

## 2. Estados mínimos del run

Estados reconocidos del run:
- `created`
- `preparing_dataset`
- `running_agent`
- `succeeded`
- `failed`

No hace falta introducir más estados mientras el producto siga simple.

---

## 3. DatasetProfile

### Propósito
Representar la metadata mínima del dataset ya validado y cargado.

### Campos
- `source_path`
- `format`
- `table_name`
- `schema`
- `row_count`
- `nulls?`
- `sample?`

### Reglas mínimas
- Corresponde exactamente al dataset del run actual.
- No contiene hallazgos ni interpretación.
- `table_name` es el identificador usable por el agente en DuckDB.

---

## 4. AgentExecutionContext

### Propósito
Agrupar el contexto estructurado mínimo que necesita el agente para ejecutar el análisis.

### Campos
- `run_id`
- `session_id`
- `dataset_profile`
- `duckdb_context`
- `output_dir`

### Reglas mínimas
- Siempre pertenece a un único `run_id`.
- Contiene un `DatasetProfile` válido.
- Apunta a un contexto DuckDB listo para consulta.
- `output_dir` pertenece al run actual.

### Nota de consistencia
El nombre congelado en esta fase sigue siendo `duckdb_context`.

---

## 5. AgentResult

### Propósito
Definir la salida estructurada del agente tras completar el análisis.

### Campos
- `narrative`
- `findings`
- `sql_trace`
- `tables`
- `charts`
- `recommendations?`
- `artifact_manifest`

### Reglas mínimas
- Pertenece a un único run.
- Se interpreta sin depender del renderer de CLI o UI.
- No incluye routing, selección automática de agente ni control de sesión.
- `findings`, `sql_trace`, `tables` y `charts` pueden venir vacíos.

### Formato esperado de `sql_trace`
Cada entrada debe incluir:
- `statement`
- `status` (`ok` o `error`)
- `purpose?`
- `rows_returned?`

---

## 6. ArtifactManifest

### Propósito
Indexar las salidas generadas por un run para mantener trazabilidad.

### Campos
- `run_id`
- `response_path?`
- `table_paths`
- `chart_paths`

### Reglas mínimas
- Solo referencia outputs del run actual.
- `table_paths` y `chart_paths` pueden venir vacíos.

### Persistencia mínima actual
- `response_path` apunta al menos a `response.md`.
- `table_paths` apunta a JSON persistidos del run actual.
- `chart_paths` puede venir vacío.

---

## 7. Contrato mínimo de errores del core

### Propósito
Dar un formato común a los errores del runtime, datos, adapters y agente.

### Campos
- `code`
- `message`
- `stage`
- `details?`

### Stages mínimos reconocibles
- `request_validation`
- `dataset_preparation`
- `agent_resolution`
- `agent_execution`
- `artifact_persistence`

---

## 8. Interfaz mínima esperada del Agent Registry

### Responsabilidad mínima
- Aceptar `agent_id`.
- Resolverlo a una implementación disponible.
- Exponer configuración estática mínima.
- Fallar si el agente no existe.

### Límites
- No enruta.
- No decide qué agente conviene.
- No reescribe prompts.
- No actúa como Planner encubierto.

---

## 9. Interfaz mínima esperada del adapter LLM

### Responsabilidad mínima
- Recibir un prompt preparado por la capa agente.
- Llamar al modelo fijo del sistema a través de Ollama.
- Devolver contenido generado.
- Traducir errores del proveedor al contrato mínimo de errores.

### Límites
- No decide el agente.
- No elige múltiples modelos o proveedores.
- No introduce fallback complejo ni routing.

---

## 10. Interfaz mínima esperada del loader/profiler de dataset

### Responsabilidad mínima
- Recibir una ruta local.
- Validar existencia y formato soportado.
- Cargar el dataset en DuckDB.
- Construir y devolver un `DatasetProfile`.
- Fallar con error claro si la validación o carga falla.

### Límites
- No resuelve múltiples datasets por run.
- No incorpora catálogo ni conectores remotos.
- No mezcla profiling técnico con hallazgos analíticos.

---

## 11. Contratos mínimos post-MVP implementados para API local y UI

Estos contratos son la superficie pública local que consumen la API y la UI en la fase producto actual.

### 11.1 CreateRunRequest

#### Propósito
Payload mínimo que recibe la API local para crear un run.

#### Campos
- `agent_id`
- `dataset_path`
- `user_prompt`
- `session_id?`

#### Regla
Debe mapear 1:1 al contrato interno `RunRequest` sin introducir semántica adicional.

### 11.2 RunSummary

#### Propósito
Representar un run en listados o vistas resumidas.

#### Campos
- `run_id`
- `session_id`
- `agent_id`
- `dataset_path`
- `status`
- `created_at`
- `updated_at`

#### Regla
No incluye el contenido completo del análisis ni reemplaza `RunDetail`.

#### Regla de persistencia
Debe alimentarse de metadata persistida localmente, no solo de memoria de proceso.

### 11.3 RunDetail

#### Propósito
Representar el detalle consultable de un run desde API/UI.

#### Campos
- `run_id`
- `session_id`
- `agent_id`
- `dataset_profile?`
- `status`
- `result?`
- `error?`
- `artifact_manifest?`
- `created_at`
- `updated_at`

#### Regla
Si el run no terminó todavía, `result` puede no existir.

#### Regla de persistencia
Debe alimentarse de metadata persistida localmente, no solo de memoria de proceso.

### 11.4 ArtifactListItem

#### Propósito
Representar un artifact individual en API/UI.

#### Campos
- `name`
- `type`
- `path`
- `run_id`
- `size_bytes?`

#### Tipos mínimos previstos
- `response`
- `table`
- `chart`

### 11.5 ChartSpec / ChartReference enriquecido

#### Propósito
Representar un gráfico renderizable directamente por la UI sin obligar al usuario a abrir JSON ni rutas de archivo.

#### Campos
- `name`
- `chart_type`
- `title?`
- `x_key?`
- `y_key?`
- `data`
- `path?`

#### Regla
`data` contiene filas ya calculadas por el agente/herramienta determinística. La UI puede renderizar SVG local a partir de esos datos. `path` sigue siendo opcional y solo existe para trazabilidad técnica si se persiste un archivo.

### 11.6 ApplicationHealth

#### Propósito
Exponer el estado operativo interno de la aplicación local antes de que exista liveness HTTP real.

#### Campos
- `status`
- `ready`
- `default_agent_id`
- `artifacts_root`
- `checks`
- `details?`

#### Regla
Representa wiring/configuración local válida del producto, no solo “servidor HTTP levantado”. `GET /health` hereda esta semántica mínima.

### 11.7 ProveedorHealth

#### Propósito
Exponer el estado operativo del proveedor local requerido por el producto.

#### Campos
- `status`
- `ready`
- `proveedor`
- `endpoint`
- `binary_available`
- `binary_path?`
- `reachable`
- `version?`
- `model`
- `model_available`
- `details?`

#### Regla
Debe servir para diagnosticar si Ollama responde y si `deepseek-r1:8b` está disponible.

### 11.8 AppConfig

#### Propósito
Exponer configuración efectiva mínima útil para la UI local.

#### Campos
- `default_agent_id`
- `supported_dataset_formats`
- `proveedor_name`
- `proveedor_endpoint`
- `required_model`

#### Regla
No debe exponer todavía secretos ni configuración enterprise.

#### Regla adicional
La CLI actual (`status` / `config`) expone esta configuración directamente y la API local mantiene el mismo shape mínimo.

### 11.9 CreateChatRequest

#### Propósito
Crear una conversación local anclada a un único `agent_id` y `dataset_path`, ejecutando la primera pregunta como un run.

#### Campos
- `agent_id`
- `dataset_path`
- `user_prompt`

#### Regla
No introduce selección automática de agente ni múltiples datasets. El chat reutiliza `session_id` como `chat_id` para agrupar runs.

### 11.10 SendChatMessageRequest

#### Propósito
Enviar una pregunta de seguimiento a un chat existente.

#### Campos
- `user_prompt`

#### Regla
El dataset y el agente se heredan del chat. No se permite cambiar dataset dentro del mismo chat en esta fase.

### 11.11 ChatMessage

#### Propósito
Representar un mensaje de usuario o respuesta del analista dentro de un chat local.

#### Campos
- `message_id`
- `role`
- `content`
- `created_at`
- `run_id?`
- `status?`
- `result?`
- `error?`

#### Regla
Los mensajes `assistant` pueden incluir `result` o `error`. Los detalles técnicos de `run_id` y artifacts siguen disponibles, pero no son el contenido principal de la UI.

### 11.12 ChatSummary

#### Propósito
Representar un chat en listados.

#### Campos
- `chat_id`
- `agent_id`
- `dataset_path`
- `title`
- `created_at`
- `updated_at`
- `latest_run_id?`
- `message_count`

### 11.13 ChatDetail

#### Propósito
Representar el chat completo con mensajes y runs asociados.

#### Campos
- `chat_id`
- `agent_id`
- `dataset_path`
- `title`
- `created_at`
- `updated_at`
- `messages`
- `run_ids`
- `latest_run_id?`

#### Regla
El chat es una capa local de producto sobre runs persistidos. No sustituye la trazabilidad por run; la agrupa para conversación.

### 11.14 ApiError

#### Propósito
Dar formato estable a errores de la API local.

#### Campos
- `code`
- `message`
- `status`
- `details?`
- `trace_id?`

#### Regla
Debe poder mapear errores del core sin perder legibilidad para UI y soporte.

#### Regla adicional de Fase 5
- `details.category` debe clasificar el error como `request`, `dataset`, `provider` o `core`.
- Cuando exista contexto adicional, debe vivir dentro de `details.context`.

### 11.15 LocalDatasetListItem

#### Propósito
Representar un archivo local seleccionable desde la UI para evitar copiar rutas habituales de `DatasetV1`.

#### Campos
- `name`
- `label`
- `path`
- `format`
- `size_bytes`

#### Regla
Este contrato es un selector local simple sobre `DatasetV1`. No carga datasets, no perfila datos, no introduce catálogo complejo y no permite usar varios datasets en un run. La UI sigue enviando un único `dataset_path` en `CreateChatRequest`.

---

## 12. Persistencia local mínima actual

La fase producto actual usa una persistencia local mínima de metadata de runs y chats con estas reglas:
- debe ser file-backed;
- debe vivir junto al espacio local de artifacts o en una ubicación equivalente del mismo entorno local;
- no requiere introducir todavía una base de datos adicional;
- debe permitir `GET /runs`, `GET /runs/{run_id}` y `GET /runs/{run_id}/artifacts` sin depender solo del proceso actual;
- debe permitir `GET /chats`, `GET /chats/{chat_id}` y continuidad conversacional local sin backend remoto.

---

## 13. Endpoints mínimos documentados actuales

### `POST /runs`
- Crea un run nuevo.
- Entrada: `CreateRunRequest`.
- Salida mínima: `RunDetail` inicial o `RunSummary` con `run_id`.
- Devuelve además header `X-Trace-Id` para correlación operativa.

### `GET /runs`
- Devuelve el listado de runs persistidos localmente.
- Salida: lista de `RunSummary`.
- Devuelve además header `X-Trace-Id`.

### `GET /runs/{run_id}`
- Devuelve el estado y detalle del run.
- Salida: `RunDetail`.
- Si el run falló, `error.details.category` debe venir persistido.
- Devuelve además header `X-Trace-Id`.

### `GET /runs/{run_id}/artifacts`
- Devuelve la lista de artifacts persistidos del run.
- Salida: lista de `ArtifactListItem`.
- Devuelve además header `X-Trace-Id`.

### `POST /chats`
- Crea un chat local y ejecuta la primera pregunta.
- Entrada: `CreateChatRequest`.
- Salida: `ChatDetail`.
- Devuelve además header `X-Trace-Id`.

### `GET /chats`
- Devuelve el listado de chats persistidos localmente.
- Salida: lista de `ChatSummary`.
- Devuelve además header `X-Trace-Id`.

### `GET /chats/{chat_id}`
- Devuelve mensajes, runs asociados y estado del chat.
- Salida: `ChatDetail`.
- Devuelve además header `X-Trace-Id`.

### `POST /chats/{chat_id}/messages`
- Añade una pregunta de seguimiento al chat y lanza un nuevo run con el mismo `session_id`.
- Entrada: `SendChatMessageRequest`.
- Salida: `ChatDetail`.
- Devuelve además header `X-Trace-Id`.

### `GET /health`
- Confirma que la aplicación/API local está levantada.
- Salida mínima: `ApplicationHealth`.
- Debe heredar la semántica operativa ya expuesta por la CLI en Fase 1.
- Devuelve además header `X-Trace-Id`.

### `GET /health/proveedor`
- Expone `ProveedorHealth`.
- Sirve para readiness del proveedor local y del modelo requerido.
- Devuelve además header `X-Trace-Id`.

### `GET /datasets/local`
- Lista archivos locales soportados (`csv`, `xlsx`, `parquet`) detectados en `DatasetV1`.
- Salida: lista de `LocalDatasetListItem`.
- Si `DatasetV1` no existe o no contiene archivos soportados, devuelve `[]`.
- Devuelve además header `X-Trace-Id`.
- No carga el dataset en DuckDB ni sustituye el contrato `dataset_path`; solo facilita la selección en la UI.

---

## 14. Límites explícitos de estos contratos
- No se diseña auth.
- No se diseña multiusuario.
- No se diseña backend remoto.
- No se diseñan colas ni workers distribuidos.
- No se diseña soporte multi-agent real.
- No se diseñan múltiples datasets por run.

La intención es fijar una API local mínima y una semántica estable para la UI, no adelantar arquitectura fuera de scope.
