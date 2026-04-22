# TEST_PLAN

## Objetivo
Definir cómo se valida el sistema en la nueva fase del producto:
- manteniendo la base de tests del core ya implementado;
- ampliando la validación para API local, UI web y operación local;
- sin mezclar pruebas del producto con alcance todavía no aprobado.

## Principio general
El MVP ya cuenta con validación del core. La fase producto actual no reemplaza esa cobertura: la **extiende**.

Las capas de validación deben quedar separadas:
- validación del core;
- validación de API local;
- validación de UI web;
- validación operativa local;
- validación de historial persistente local;
- validación de release/packaging cuando llegue el momento.

---

## 1. Validación del core existente

### Objetivo
Seguir protegiendo el comportamiento ya implementado del núcleo del sistema.

### Debe cubrir
- contratos del flujo (`RunRequest`, `DatasetProfile`, `AgentExecutionContext`, `AgentResult`, `ArtifactManifest`);
- validaciones básicas de entrada;
- resolución del `Agent Registry`;
- gestión de sesión, `run_id` y estados del run;
- profiling mínimo del dataset;
- validación de formatos soportados: `csv`, `xlsx`, `parquet`;
- construcción del `ArtifactManifest`;
- mapeo del contrato mínimo de errores.

### Comandos de referencia
- `pytest tests/unit -q`
- `pytest tests/integration -q`
- `pytest tests/e2e -q`

---

## 2. Validación de API local

### Objetivo
Comprobar que la API local reutiliza el core correctamente y expone contratos consistentes.

### Debe cubrir
- `POST /runs` con solicitud válida usando `dataset_path` manual;
- `POST /chats` para crear una conversación local con primer run;
- `GET /chats` y `GET /chats/{chat_id}` para historial conversacional;
- `POST /chats/{chat_id}/messages` para seguimiento con el mismo `session_id`;
- rechazo claro de payload inválido;
- `GET /runs` para listado de runs persistidos localmente;
- `GET /runs/{run_id}` para estados y detalle;
- `GET /runs/{run_id}/artifacts`;
- `GET /health`;
- `GET /health/proveedor`;
- mapeo consistente de errores del core a `ApiError`.
- header `X-Trace-Id` en respuestas.
- `details.category` en errores API.

### Tipos de prueba esperados
- contract tests de request/response;
- integration tests de API + core;
- tests de errores operativos del proveedor local.

### Comando de referencia actual
- `pytest tests/integration/test_api_endpoints.py -q`

---

## 3. Validación de UI web

### Objetivo
Demostrar que la experiencia principal del producto funciona de forma completa.

### Debe cubrir
- pantalla o estado de readiness;
- historial persistente visible desde la carga inicial;
- selección de un run previo desde la UI;
- lanzamiento de un run desde la UI;
- entrada por ruta manual local al dataset;
- visualización de narrativa y hallazgos;
- visualización de gráficos embebidos sin exponer JSON/rutas como contenido principal;
- acceso a artifacts/exportaciones técnicas del run de forma colapsada;
- refresco del historial tras crear un chat o enviar un seguimiento;
- errores claros cuando falte proveedor, modelo o dataset válido.

### Tipos de prueba esperados
- tests de componentes si aportan valor;
- browser E2E como validación principal del flujo;
- smoke UI + API + core cuando la interfaz ya exista.

### Herramienta prevista
- Playwright para browser E2E.

### Comandos de referencia actuales
- `npm --prefix interfaces/web run build`
- `npm --prefix interfaces/web run test:e2e`
- smoke manual real: API local + UI local con `DatasetV1/demo_business_metrics.csv`

---

## 4. Validación de historial persistente local

### Objetivo
Asegurar que el sistema puede listar y recuperar chats/runs más allá del proceso actual.

### Debe cubrir
- persistencia file-backed mínima de metadata de chats;
- persistencia file-backed mínima de metadata de runs;
- `GET /chats` con resultados coherentes;
- `GET /chats/{chat_id}` con mensajes y runs asociados;
- `GET /runs` con resultados coherentes;
- `GET /runs/{run_id}` sobre runs persistidos;
- consistencia entre historial y artifacts reales;
- exposición del historial persistido de chats en la UI sin bloquearse por readiness del proveedor;
- disponibilidad del historial tras reinicio del proceso cuando la metadata persistida existe.

### Casos críticos
- metadata persistida existe pero faltan artifacts;
- artifact existe pero falta metadata del run;
- historial vacío sin error;
- run persistido con estado fallido;
- consulta de `run_id` inexistente.

### Comando de referencia actual
- `pytest tests/integration/test_api_endpoints.py -q`
- `npm --prefix interfaces/web run test:e2e`

---

## 5. Validación operativa local

### Objetivo
Asegurar que el producto es usable en un entorno real local-first.

### Debe cubrir
- binario `ollama` disponible en PATH cuando aplique;
- servicio accesible en `127.0.0.1:11434`;
- modelo `deepseek-r1:8b` disponible;
- mensajes accionables cuando falle readiness;
- coherencia entre estado real y estado expuesto por la aplicación.
- correlación mínima por `trace_id`, `session_id` y `run_id` en logs JSON.

### Casos críticos
- Ollama no instalado;
- Ollama instalado pero apagado;
- Ollama accesible pero modelo ausente;
- dataset inexistente o formato no soportado;
- artifact esperado ausente tras un run fallido.

---

## 6. Smoke tests reales

### Objetivo
Confirmar la integración mínima real del sistema con dependencias locales.

### Núcleo actual que se mantiene
- smoke del adapter real con Ollama;
- smoke E2E real de CLI.

### Evolución prevista
Cuando exista API/UI, añadir smoke explícito para:
- aplicación local levantada;
- API local respondiendo;
- proveedor local listo;
- roundtrip mínimo desde la superficie principal.

### Regla
Los smoke tests reales siguen siendo pocos, explícitos y separados del ciclo rápido de desarrollo.

---

## 7. Validación de setup y readiness

### Objetivo
Comprobar que la experiencia de arranque del producto es comprensible y verificable.

### Debe cubrir
- lectura de configuración efectiva;
- endpoint o chequeo de health de aplicación;
- endpoint o chequeo de health del proveedor;
- errores de configuración mínimos;
- consistencia entre documentación operativa y comportamiento real.

### Chequeos actuales mínimos
- `python -m interfaces.cli status`
- `python -m interfaces.cli status --json`
- `python -m interfaces.cli config`
- `python -m interfaces.cli config --json`
- `curl http://127.0.0.1:8000/health`
- `curl http://127.0.0.1:8000/health/proveedor`

### Casos críticos específicos
- `status` devuelve exit code no-cero cuando el sistema no está listo;
- `status --json` mantiene un shape estable con `application`, `provider`, `issues` y `ready`;
- `config` no expone secretos;
- los smokes de proveedor reutilizan la misma base de probes que la CLI operativa.
- la salida humana de CLI no se contamina con logs estructurados.
- los logs JSON de consola conservan `trace_id` y, cuando aplica, `session_id`/`run_id`.

---

## 8. Validación de packaging y release

### Objetivo
Preparar la etapa en la que el producto se distribuya de forma más formal.

### Debe cubrir
- instalación reproducible;
- arranque reproducible;
- ejecución repo-local de lanes automáticos (`python` + `web`);
- separación explícita entre validación automatizable y smoke real/manual;
- serving de la UI build desde la API local;
- fallo claro cuando falta `interfaces/web/dist`;
- smoke manual documentado del arranque monoproceso;
- verificación de que la documentación de operación coincide con el empaquetado real.

### Comandos de referencia actuales
- `python scripts/ci_checks.py python`
- `python scripts/ci_checks.py web`
- `python scripts/ci_checks.py smoke`
- validación manual: `python -m interfaces.api --serve-web`

---

## Fixtures y datasets de prueba
La estrategia actual sigue siendo válida:
- datasets temporales creados dentro de tests para `csv`, `xlsx`, `parquet`, vacío y corrupto;
- `DatasetV1/demo_business_metrics.csv` como dataset de referencia del repo para integración y validación manual.

Uso esperado:
- datasets temporales para validar invariantes y errores;
- dataset de referencia para smoke/manual y flujos integrados.

---

## Escenarios críticos obligatorios

### Core
- ruta inexistente;
- formato no soportado;
- archivo vacío o corrupto;
- selección de agente desconocido;
- continuación de sesión con `session_id`.

### API
- payload inválido;
- `run_id` inexistente;
- error del proveedor propagado con formato estable;
- endpoints de health coherentes con estado real;
- listado de runs persistidos localmente.

### UI
- el usuario ve claramente si el sistema está listo;
- el usuario puede lanzar un run válido usando ruta manual local;
- el usuario puede distinguir resultado válido de error operativo;
- el usuario puede localizar artifacts.

### Historial
- el historial persiste si la metadata local existe;
- el listado de runs no depende solo del proceso actual.
- la UI puede abrir un run previo ya persistido.
- la UI sigue pudiendo explorar historial aunque readiness bloquee nuevos submits.

### Operación
- el sistema no finge readiness si Ollama no está listo;
- el sistema indica si falta el modelo requerido.

---

## Criterio de aceptación de la fase producto actual
La fase producto se considera bien encaminada cuando:
- el core siga validado;
- la API local sea comprobable por tests;
- la UI web sea validable con browser E2E;
- el historial persistente local sea comprobable;
- el estado operativo local sea visible y confiable;
- los smoke reales sigan siendo explícitos y reproducibles;
- exista un runner repo-local único para lanes automáticos y smokes reales.

## Comandos de verificación de referencia
La Fase 7 deja un runner formal repo-local:
- lane automático Python: `python scripts/ci_checks.py python`
- lane automático Web: `python scripts/ci_checks.py web`
- lane real/local con Ollama: `python scripts/ci_checks.py smoke`

Cobertura directa de cada lane:
- `python`:
  - `pytest tests/unit -q`
  - `pytest tests/integration -q`
  - `pytest tests/e2e -q`
- `web`:
  - `npm --prefix interfaces/web run build`
  - `npm --prefix interfaces/web run test:e2e`
- `smoke`:
  - `pytest tests/smoke/test_ollama_adapter.py -q -rs`
  - `pytest tests/smoke/test_cli_status.py -q -rs`
  - `pytest tests/smoke/test_real_cli_workflow.py -q -rs`

Validaciones complementarias que siguen siendo obligatorias para release:
- smoke manual de packaging local: `python -m interfaces.api --serve-web`
- verificación manual del flujo UI empaquetado desde `http://127.0.0.1:8000/`

Nota operativa:
- en este entorno Windows sandbox, `npm --prefix interfaces/web run build` puede fallar con `spawn EPERM`; la validación real del lane `web` debe ejecutarse en host real o en CI.
