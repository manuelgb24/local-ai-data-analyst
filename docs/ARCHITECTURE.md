# ARCHITECTURE

## Visión general
La arquitectura de `3_agents` entra en una nueva etapa: el **core analítico del MVP ya existe** y pasa a ser la base estable del producto.

El objetivo ahora es añadir una **interfaz web principal** y una **API local** sin romper el flujo ya validado por CLI. El producto sigue siendo **local-first**: el dataset vive en la máquina del usuario, DuckDB corre en local y Ollama sigue siendo un prerequisito local explícito.

## Principio rector
La UI y la API se apoyan en el mismo core existente. No deben reimplementar:
- validación del run;
- preparación del dataset;
- tracking de sesión/run;
- resolución del agente;
- persistencia de artifacts;
- integración con DuckDB y Ollama.

## Capas del sistema y responsabilidades

### 1. `interfaces/web`
- Superficie principal del producto.
- Permite crear chats analíticos locales por dataset, revisar resultados, hacer preguntas de seguimiento, consultar historial persistido y ver estado operativo.
- No implementa lógica analítica.
- Consume la API local del mismo repositorio.
- La entrada documentada del dataset en esta fase sigue siendo un único `dataset_path` local; la UI puede facilitarlo con un selector simple de archivos en `DatasetV1` y fallback de ruta manual.
- Trata `run_id`, rutas de artifacts y trazas SQL como detalles técnicos colapsables, no como contenido principal.

### 2. `interfaces/api`
- Expone contratos locales para el producto.
- Publica endpoints mínimos de chats, ejecución, listado de runs, consulta de runs, artifacts y health.
- Traduce peticiones externas al caso de uso del sistema.
- Recibe un `dataset_path` local, ya sea escrito manualmente o seleccionado desde `DatasetV1`, y construye el `RunRequest` interno.
- En Fase 6 puede servir además la UI build en modo monoproceso para reducir fricción de arranque local.
- No duplica lógica de runtime o agente.

### 3. `interfaces/cli`
- Se mantiene como interfaz operativa y técnica.
- Sirve para validación manual, smoke tests y soporte.
- Debe seguir reutilizando el mismo caso de uso principal.

### 4. `application`
- Contiene los casos de uso del sistema.
- Es la frontera estable entre interfaces y core de ejecución.
- Debe seguir siendo reutilizable por CLI, API y futuras interfaces.
- Mantiene la capa local de chat como agrupación de runs por `session_id`.

### 5. `runtime`
- Coordina la ejecución del run.
- Crea o recupera sesión.
- Crea el run y gestiona sus estados.
- Resuelve el agente mediante el `Agent Registry`.
- Coordina la preparación del dataset, la ejecución del agente y la persistencia de outputs.
- En la evolución prevista deberá apoyarse en metadata persistida localmente para exponer historial de runs.

### 6. `agents/data_analyst`
- Único agente real del sistema en esta fase.
- Analiza el dataset ya preparado.
- Produce una salida estructurada, trazable y visualizable.
- Puede usar herramientas DuckDB determinísticas acotadas para rankings, agregaciones por grupo y correlaciones simples.
- No ejecuta SQL libre generado por el LLM.

### 7. `data`
- Valida ruta y formato.
- Carga el dataset en DuckDB.
- Genera metadata mínima del dataset.
- Deja el dataset listo para consulta del agente.

### 8. `artifacts`
- Persiste la respuesta y outputs del run.
- Mantiene el manifiesto de artifacts.
- Debe poder servir tanto a CLI como a API/UI.
- Comparte espacio conceptual con la persistencia local mínima de metadata de runs y chats.

### 9. `adapters`
- Aíslan integraciones con DuckDB, Ollama y filesystem.
- No arrancan procesos locales ni hacen auto-start del proveedor.
- Traducen errores de dependencias externas a contratos del sistema.

### 10. `observability`
- Debe cubrir logs estructurados, correlación por `session_id` y `run_id`, health y readiness.
- Debe crecer como capacidad transversal del producto, no como lógica de interfaz.
- Desde la Fase 1 ya puede alojar un servicio compartido de readiness/configuración reutilizable por CLI ahora y por API/UI más adelante.
- Desde la Fase 5 centraliza además logs JSON a consola, `trace_id` por request/comando y clasificación mínima de errores (`request`, `dataset`, `provider`, `core`).

## Flujos principales

### Flujo principal del producto
1. La UI local crea o selecciona un chat.
2. La API recibe `agent_id`, `dataset_path` y `user_prompt` al crear chat, o solo `user_prompt` en un seguimiento.
3. `application` fija el chat a un único dataset/agente y lanza un run con `session_id = chat_id`.
4. `runtime` valida, crea run y coordina el flujo.
5. `data` carga y perfila el dataset.
6. `runtime` construye el contexto del agente.
7. `data_analyst` analiza el dataset usando DuckDB, herramientas determinísticas acotadas y Ollama.
8. `artifacts` persiste la respuesta y outputs.
9. La persistencia local de metadata permite listar y consultar runs y chats posteriores.
10. La API devuelve `ChatDetail` con mensajes, resultados y referencias técnicas.
11. La UI renderiza conversación, narrativa, gráficos embebidos y detalles técnicos colapsados.

### Flujo repo-local empaquetado
1. Se construye `interfaces/web/dist`.
2. `python -m interfaces.api --serve-web` levanta un único proceso local.
3. Ese proceso sirve la UI build en `/` y mantiene la API local en el mismo origen.
4. La UI empaquetada consume `/health`, `/health/proveedor`, `/chats*` y `/runs*` sin proxy de desarrollo.

### Flujo operativo por CLI
1. La CLI puede exponer `status`, `config` y `run`.
2. `status`/`config` llaman a casos de uso ligeros de `application` apoyados en `observability`.
3. `run` recibe `agent_id`, `dataset_path`, `user_prompt` y `session_id?`.
4. `application` invoca el mismo caso de uso principal.
5. El resto del flujo es idéntico al producto.

## Health y readiness
El producto necesita dos superficies operativas explícitas:
- **health de aplicación**: en Fase 1 confirma que el wiring/config local del producto es válido y que la superficie local puede operar; cuando exista API, esta semántica se reutiliza en `GET /health`;
- **health del proveedor**: confirma que Ollama responde y que el modelo requerido está disponible.

Esto no cambia el core analítico, pero sí forma parte de la arquitectura del producto.

## Correlación operativa mínima
La observabilidad mínima del producto queda distribuida así:
- **API local**: genera `trace_id` por request, lo devuelve en `X-Trace-Id` y lo conserva en el cuerpo de errores.
- **CLI**: genera `trace_id` por comando, mantiene salida humana estable y deja la telemetría técnica en logs JSON de consola.
- **Runtime**: añade `session_id` y `run_id` a los eventos del ciclo de vida del run (`run_started`, `dataset_preparing`, `agent_running`, `run_succeeded`, `run_failed`).

La correlación cruza `interfaces/api` o `interfaces/cli` con `runtime` sin introducir un backend remoto ni persistencia nueva de logs.

## Papel del runtime
El `runtime` sigue siendo la pieza central del sistema. Su responsabilidad no cambia:
- coordinar el run;
- gestionar sesión y tracking;
- preparar el dataset;
- resolver el agente;
- invocar al agente;
- cerrar el run con resultado o error.

El `runtime` **no**:
- decide qué agente conviene;
- hace routing;
- interpreta intención del usuario;
- incorpora lógica de UI;
- expone HTTP directamente.

## Papel de los chats locales
Los chats son una capa de producto local sobre runs persistidos:
- agrupan varios runs mediante `session_id = chat_id`;
- guardan una memoria corta de mensajes para dar continuidad a preguntas de seguimiento;
- no cambian el agente ni el dataset dentro del chat;
- no son Planner, routing automático, RAG ni multi-agent.

## Papel del Agent Registry
El `Agent Registry` sigue siendo ligero:
- acepta `agent_id`;
- resuelve la implementación disponible;
- devuelve configuración estática mínima;
- falla con error claro si el agente no existe.

No es un planner encubierto ni una capa de routing.

## Estructura objetivo del monorepo
Sin reabrir la arquitectura del core, la dirección documental del repositorio pasa a ser:
- `interfaces/web`
- `interfaces/api`
- `interfaces/cli`
- `application`
- `runtime`
- `agents/data_analyst`
- `data`
- `artifacts`
- `adapters`
- `observability`
- `tests`

## Límites actuales del producto
- Un solo agente real: `data_analyst`.
- Un único dataset por run.
- Solo archivos locales soportados mediante ruta manual.
- El selector de `DatasetV1` es una ayuda de UI/API local, no un catálogo complejo ni soporte multi-dataset.
- Solo DuckDB como motor.
- Solo Ollama local como proveedor del modelo.
- Sin multi-agent real.
- Sin auth ni multiusuario.
- Sin backend hosted.
- Sin RAG ni catálogo avanzado.

## Evolución permitida a continuación
Sin comprometer el core actual, esta arquitectura permite:
- mejorar UI web local;
- extender API local estable;
- añadir historial persistente local de runs y chats;
- mejorar observabilidad y health/readiness;
- preparar packaging y distribución local;
- reforzar CI y release.

La regla sigue siendo la misma: **hacer crecer el producto sin rehacer el core**.
