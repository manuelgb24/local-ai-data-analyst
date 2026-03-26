# TEST_PLAN

## Objetivo
Definir cómo se validará el vertical slice del MVP de forma operativa y proporcionada, sin inflar el alcance ni mezclar pruebas del core con pruebas de piezas fuera del MVP.

## Estrategia de tests unitarios
Los tests unitarios deben centrarse en piezas pequeñas, deterministas y rápidas:
- contratos del flujo (`RunRequest`, `DatasetProfile`, `AgentExecutionContext`, `AgentResult`, `ArtifactManifest`);
- validaciones básicas de entrada;
- resolución del `Agent Registry`;
- gestión de sesión, `run_id` y estados mínimos del run;
- profiling mínimo del dataset;
- validación de formatos soportados: `csv`, `xlsx`, `parquet`;
- construcción del `ArtifactManifest`;
- mapeo del contrato mínimo de errores.

Objetivo de esta capa:
- detectar reglas rotas pronto;
- proteger invariantes del MVP;
- evitar que la integración descubra errores triviales.

Comandos de referencia (`pytest` provisional):
- `pytest tests/unit -q`
- `pytest tests/unit/test_contracts.py -q`
- `pytest tests/unit/test_agent_registry.py -q`
- `pytest tests/unit/test_runtime_tracking.py -q`
- `pytest tests/unit/test_artifact_manifest.py -q`

## Estrategia de integración
Los tests de integración deben validar que las piezas principales colaboran correctamente:
- validación y carga de archivos `csv`, `xlsx` y `parquet` en DuckDB;
- construcción de `DatasetProfile` a partir del dataset cargado;
- ejecución del caso de uso principal;
- paso del contexto estructurado al agente;
- continuidad de sesión cuando llega `session_id` opcional;
- generación y localización de outputs del run.

Objetivo de esta capa:
- comprobar que el flujo entre core, datos, adapters y agente se mantiene coherente;
- validar errores reales de frontera entre componentes.

Comandos de referencia (`pytest` provisional):
- `pytest tests/integration -q`
- `pytest tests/integration/test_dataset_loading.py -q`
- `pytest tests/integration/test_dataset_profile.py -q`
- `pytest tests/integration/test_runtime_flow.py -q`
- `pytest tests/integration/test_session_continuation.py -q`
- `pytest tests/integration/test_artifact_persistence.py -q`

## Estrategia end-to-end
Los tests E2E deben cubrir el flujo completo del MVP:
1. entrada por CLI;
2. recepción de `agent_id`, `dataset_path`, `user_prompt` y `session_id` opcional;
3. preparación del dataset;
4. ejecución del agente;
5. generación de salida estructurada;
6. render final y trazabilidad del run.

Objetivo de esta capa:
- demostrar que el vertical slice funciona como experiencia completa;
- validar el producto, no solo las piezas aisladas.

Comandos de referencia (`pytest` provisional):
- `pytest tests/e2e -q`
- `pytest tests/e2e/test_cli_run.py -q`

Comando manual de referencia para CLI:
- `python -m interfaces.cli --agent data_analyst --dataset tests/fixtures/datasets/sample_valid.csv --prompt "Resume los hallazgos principales"`

## Estrategia de validación del LLM

### Tests con mocks o dobles
La mayor parte de las pruebas del agente y del adapter LLM deben usar mocking o dobles para validar:
- construcción del prompt y control de flujo del agente;
- manejo de errores del adapter;
- mapeo del error del proveedor al contrato mínimo de errores;
- construcción coherente de `AgentResult` y `ArtifactManifest` sin depender del modelo real.

Comandos de referencia (`pytest` provisional):
- `pytest tests/unit/test_llm_adapter.py -q`
- `pytest tests/integration/test_data_analyst_with_fake_llm.py -q`

### Smoke tests con Ollama real
Los smoke tests con Ollama real deben ser pocos, explícitos y separados del ciclo rápido de desarrollo. Su objetivo es confirmar solo la integración mínima con el modelo fijo del MVP.

Deben validar:
- disponibilidad básica de Ollama en local;
- disponibilidad del modelo configurado para el MVP;
- llamada mínima exitosa del adapter real.

Comandos de referencia (`pytest` provisional):
- `pytest tests/smoke/test_ollama_adapter.py -q`
- `pytest tests/smoke/test_real_model_roundtrip.py -q`

Estos smoke tests no sustituyen los tests con mocks y no deben ejecutarse por defecto para cambios que no toquen adapter, agente o integración real del modelo.

## Fixtures o datasets de prueba propuestos
Propuesta mínima de fixtures para mantener el plan simple y útil:
- `tests/fixtures/datasets/sample_valid.csv`
- `tests/fixtures/datasets/sample_valid.xlsx`
- `tests/fixtures/datasets/sample_valid.parquet`
- `tests/fixtures/datasets/empty.csv`
- `tests/fixtures/datasets/unsupported.txt`

Uso esperado:
- `sample_valid.*`: validar carga, profiling y flujo feliz;
- `empty.csv`: validar fallo controlado por dataset vacío;
- `unsupported.txt`: validar rechazo de formato fuera del MVP.

Referencia opcional:
- `DatasetV1/Walmart_Sales.csv` puede usarse para smoke tests o E2E manuales, pero no debe convertirse en fixture base obligatoria.

## Escenarios críticos obligatorios

### Ruta inexistente
- El sistema debe rechazar la ejecución con un error claro y trazable.

### Formato no soportado
- El sistema debe indicar que el formato no forma parte del MVP.

### Archivo vacío o corrupto
- El sistema debe fallar de forma controlada y no continuar el run como si fuera válido.

### Dataset válido con columnas simples
- El sistema debe poder cargarlo, perfilarlo y dejarlo listo para análisis.

### Run reproducible con manifest generado
- Una ejecución válida debe producir identificación de run y un `ArtifactManifest` consistente.

### Selección de agente desconocido
- El sistema debe rechazar `agent_id` no registrados sin intentar un fallback implícito.

### `session_id` opcional / continuación de sesión
- El sistema debe aceptar runs nuevos sin `session_id` y también continuar una sesión existente cuando ese campo llegue informado.

## Criterio de aceptación del vertical slice
El vertical slice del MVP se considera aceptado cuando, sobre un archivo local real:
- el usuario puede indicar un agente válido y un dataset válido;
- el sistema ejecuta el flujo completo sin intervención manual adicional;
- el análisis devuelve una salida estructurada útil;
- existe trazabilidad mínima por sesión y run;
- los outputs del run quedan localizables mediante un manifiesto;
- ningún paso depende de Planner, routing automático, multi-agent real o infraestructura fuera de scope.

## Notas de alcance
Este plan de pruebas no cubre todavía:
- frontend;
- API;
- pruebas multiusuario;
- RAG;
- varios datasets por run;
- interacción entre múltiples agentes;
- CI/CD o automatización de pipelines.

## Comandos de verificación
Antes de dar una tarea por cerrada, Codex debe ejecutar solo la validación mínima que corresponda al cambio realizado:
- cambios en contratos, validaciones o tracking: `pytest tests/unit -q`
- cambios en carga de datos, profiling, runtime o persistencia: `pytest tests/integration -q`
- cambios que afecten el flujo completo o la CLI: `pytest tests/e2e -q`
- cambios que afecten adapter LLM o integración real con modelo: `pytest tests/smoke/test_ollama_adapter.py -q`

Mientras el repo no formalice otro runner, estos comandos deben tomarse como referencia inicial con `pytest`.
