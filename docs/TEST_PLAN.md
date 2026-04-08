# TEST_PLAN

## Objetivo
Definir cómo se valida el sistema en la nueva fase del producto:
- manteniendo la base de tests del core ya implementado;
- ampliando la validación para API local, UI web y operación local;
- sin mezclar pruebas del producto con alcance todavía no aprobado.

## Principio general
El MVP ya cuenta con validación del core. La siguiente fase no reemplaza esa cobertura: la **extiende**.

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
- rechazo claro de payload inválido;
- `GET /runs` para listado de runs persistidos localmente;
- `GET /runs/{run_id}` para estados y detalle;
- `GET /runs/{run_id}/artifacts`;
- `GET /health`;
- `GET /health/proveedor`;
- mapeo consistente de errores del core a `ApiError`.

### Tipos de prueba esperados
- contract tests de request/response;
- integration tests de API + core;
- tests de errores operativos del proveedor local.

---

## 3. Validación de UI web

### Objetivo
Demostrar que la experiencia principal del producto funciona de forma completa.

### Debe cubrir
- pantalla o estado de readiness;
- lanzamiento de un run desde la UI;
- entrada por ruta manual local al dataset;
- visualización de narrativa y hallazgos;
- acceso a artifacts del run;
- errores claros cuando falte proveedor, modelo o dataset válido.

### Tipos de prueba esperados
- tests de componentes si aportan valor;
- browser E2E como validación principal del flujo;
- smoke UI + API + core cuando la interfaz ya exista.

### Herramienta prevista
- Playwright para browser E2E.

---

## 4. Validación de historial persistente local

### Objetivo
Asegurar que el sistema puede listar y recuperar runs más allá del proceso actual.

### Debe cubrir
- persistencia file-backed mínima de metadata de runs;
- `GET /runs` con resultados coherentes;
- `GET /runs/{run_id}` sobre runs persistidos;
- consistencia entre historial y artifacts reales;
- disponibilidad del historial tras reinicio del proceso cuando la metadata persistida existe.

### Casos críticos
- metadata persistida existe pero faltan artifacts;
- artifact existe pero falta metadata del run;
- historial vacío sin error;
- run persistido con estado fallido;
- consulta de `run_id` inexistente.

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

### Casos críticos específicos
- `status` devuelve exit code no-cero cuando el sistema no está listo;
- `status --json` mantiene un shape estable con `application`, `provider`, `issues` y `ready`;
- `config` no expone secretos;
- los smokes de proveedor reutilizan la misma base de probes que la CLI operativa.

---

## 8. Validación de packaging y release

### Objetivo
Preparar la etapa en la que el producto se distribuya de forma más formal.

### Debe cubrir cuando se implemente
- instalación reproducible;
- arranque reproducible;
- checks previos a release;
- smoke manual documentado;
- verificación de que la documentación de operación coincide con el empaquetado real.

---

## Fixtures y datasets de prueba
La estrategia actual sigue siendo válida:
- datasets temporales creados dentro de tests para `csv`, `xlsx`, `parquet`, vacío y corrupto;
- `DatasetV1/Walmart_Sales.csv` como dataset de referencia del repo para integración y validación manual.

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

### Operación
- el sistema no finge readiness si Ollama no está listo;
- el sistema indica si falta el modelo requerido.

---

## Criterio de aceptación de la siguiente fase
La fase producto se considerará bien encaminada cuando:
- el core siga validado;
- la API local sea comprobable por tests;
- la UI web sea validable con browser E2E;
- el historial persistente local sea comprobable;
- el estado operativo local sea visible y confiable;
- los smoke reales sigan siendo explícitos y reproducibles.

## Comandos de verificación de referencia
Mientras no exista otro runner formal:
- core unitario: `pytest tests/unit -q`
- core integración: `pytest tests/integration -q`
- core E2E actual: `pytest tests/e2e -q`
- smoke adapter real: `pytest tests/smoke/test_ollama_adapter.py -q -rs`
- smoke CLI real: `pytest tests/smoke/test_real_cli_workflow.py -q -rs`

Cuando aparezcan API y UI, deberán añadirse sus comandos de referencia a este documento antes de dar esa fase por cerrada.
