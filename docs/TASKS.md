# TASKS

## Propósito
Este documento ordena la implementación del vertical slice del MVP en fases pequeñas, secuenciales y verificables. Se apoya en `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/CONTRACTS.md` y `docs/TEST_PLAN.md`, pero no redefine esos documentos.

## Uso
- Ejecutar las fases en orden.
- No abrir nuevas líneas de trabajo hasta validar la fase actual.
- Si una fase obliga a cambiar contratos o arquitectura, actualizar primero la documentación fuente de verdad correspondiente.

---

## Fase 1
- **Nombre**: Scaffold y estructura base del repo.
- **Objetivo**: crear la estructura mínima del proyecto alineada con la arquitectura aprobada para poder implementar el vertical slice sin mezclar responsabilidades.
- **Archivos o carpetas previsiblemente afectadas**: `interfaces/cli`, `application`, `runtime`, `agents/data_analyst`, `data`, `artifacts`, `adapters`, `tests`.
- **Criterios de aceptación**:
  - existe la estructura base del repo;
  - la separación entre capas coincide con `AGENTS.md` y `docs/ARCHITECTURE.md`;
  - no aparecen carpetas o módulos fuera del alcance del MVP.
- **Validación mínima**: revisar el árbol de carpetas y comprobar que la ruta principal permitida del MVP queda representada.

## Fase 2
- **Nombre**: Contratos y modelos base.
- **Objetivo**: materializar en código los contratos y tipos mínimos definidos en `docs/CONTRACTS.md` sin añadir abstracciones fuera del MVP.
- **Archivos o carpetas previsiblemente afectadas**: `application`, `runtime`, `agents`, `data`, `artifacts`, `tests`.
- **Criterios de aceptación**:
  - existen implementaciones base para `RunRequest`, `DatasetProfile`, `AgentExecutionContext`, `AgentResult` y `ArtifactManifest`;
  - quedan representados los estados mínimos del run y el contrato mínimo de errores;
  - los modelos no introducen campos o jerarquías ajenas al MVP.
- **Validación mínima**: ejecutar tests unitarios de invariantes básicas de contratos y errores.

## Fase 3
- **Nombre**: Runtime + session/run tracking.
- **Objetivo**: implementar el flujo mínimo que recibe `RunRequest`, crea o continúa `session_id`, crea `run_id`, gestiona estados del run y coordina la ejecución sin conocer detalles de infraestructura concreta.
- **Archivos o carpetas previsiblemente afectadas**: `application`, `runtime`, `tests`.
- **Criterios de aceptación**:
  - el runtime acepta una solicitud válida y abre un run trazable;
  - el tracking usa como mínimo `created`, `preparing_dataset`, `running_agent`, `succeeded` y `failed`;
  - la coordinación del flujo no invade CLI, loader, adapter LLM ni agente.
- **Validación mínima**: tests unitarios del tracking y una integración básica del caso de uso principal.

## Fase 4
- **Nombre**: Carga y profiling de datasets en DuckDB.
- **Objetivo**: validar ruta y formato, cargar `csv`, `xlsx` y `parquet` en DuckDB y construir un `DatasetProfile` consistente para el run actual.
- **Archivos o carpetas previsiblemente afectadas**: `data`, `adapters`, `runtime`, `tests`.
- **Criterios de aceptación**:
  - un dataset local válido queda cargado y disponible para consulta;
  - `DatasetProfile` contiene al menos `source_path`, `format`, `table_name`, `schema` y `row_count`;
  - fallan de forma controlada la ruta inexistente, el formato no soportado y el archivo vacío o corrupto.
- **Validación mínima**: tests de integración con archivo real y casos de error de ruta/formato.

## Fase 5
- **Nombre**: Agent Registry mínimo.
- **Objetivo**: resolver `agent_id` explícito a la implementación disponible del MVP y devolver un error estable cuando el agente no exista.
- **Archivos o carpetas previsiblemente afectadas**: `runtime`, `agents`, `tests`.
- **Criterios de aceptación**:
  - `data_analyst` se resuelve correctamente;
  - un `agent_id` desconocido falla sin fallback implícito;
  - el registry sigue siendo una pieza ligera y no actúa como Planner ni routing automático.
- **Validación mínima**: tests unitarios de resolución correcta y rechazo de agente desconocido.

## Fase 6
- **Nombre**: Adapter LLM + integración con Ollama.
- **Objetivo**: implementar el adapter mínimo que invoque el modelo fijo del MVP vía Ollama y traduzca errores del proveedor al contrato mínimo de errores.
- **Archivos o carpetas previsiblemente afectadas**: `adapters`, `agents/data_analyst`, `tests`.
- **Criterios de aceptación**:
  - el adapter acepta un prompt ya preparado y devuelve contenido del modelo;
  - los errores del proveedor quedan mapeados a un error consistente del sistema;
  - no se introduce multi-modelo, fallback ni selección dinámica de proveedor.
- **Validación mínima**: tests con doble o mocking del adapter y smoke test local separado con Ollama real.

## Fase 7
- **Nombre**: Agente `data_analyst`.
- **Objetivo**: implementar el único agente real del MVP para que consuma `AgentExecutionContext`, consulte DuckDB, use el adapter LLM y produzca un `AgentResult` consistente.
- **Archivos o carpetas previsiblemente afectadas**: `agents/data_analyst`, `data`, `adapters`, `tests`.
- **Criterios de aceptación**:
  - el agente funciona solo con el contexto estructurado del run;
  - el resultado incluye `narrative`, `findings`, `sql_trace`, `tables`, `charts` y `artifact_manifest` con formato coherente;
  - el agente no incorpora lógica de CLI, routing ni multi-agent.
- **Validación mínima**: tests de integración del agente con dobles del adapter LLM y dataset cargado en DuckDB.

## Fase 8
- **Nombre**: Artifacts + manifest.
- **Objetivo**: persistir los outputs mínimos del run y construir un `ArtifactManifest` consistente y trazable por `run_id`.
- **Archivos o carpetas previsiblemente afectadas**: `artifacts`, `runtime`, `agents/data_analyst`, `tests`.
- **Criterios de aceptación**:
  - el run puede persistir respuesta final y outputs tabulares o gráficos cuando existan;
  - `ArtifactManifest` referencia solo outputs del run actual;
  - el manifiesto puede viajar dentro de `AgentResult` sin absorber su responsabilidad.
- **Validación mínima**: tests unitarios del manifest y una integración simple de persistencia de outputs.

## Fase 9
- **Nombre**: CLI end-to-end.
- **Objetivo**: implementar la CLI mínima que reciba `agent_id`, `dataset_path`, `user_prompt` y `session_id?`, invoque el caso de uso principal y renderice la salida estructurada.
- **Archivos o carpetas previsiblemente afectadas**: `interfaces/cli`, `application`, `runtime`, `tests`.
- **Criterios de aceptación**:
  - la CLI permite lanzar el flujo completo del MVP;
  - el render final muestra una respuesta útil y referencias trazables a outputs del run;
  - no se acopla lógica de negocio específica al parser o renderer de CLI.
- **Validación mínima**: prueba end-to-end local del comando principal con un dataset real.

## Fase 10
- **Nombre**: Tests unitarios, integración y smoke tests mínimos.
- **Objetivo**: cerrar la cobertura mínima necesaria del vertical slice siguiendo `docs/TEST_PLAN.md` y separando claramente unitarios, integración y smoke tests.
- **Archivos o carpetas previsiblemente afectadas**: `tests`, `application`, `runtime`, `data`, `agents/data_analyst`, `adapters`, `artifacts`, `interfaces/cli`.
- **Criterios de aceptación**:
  - quedan cubiertos contratos, validaciones de entrada, Agent Registry, tracking, carga y profiling, artifacts y flujo CLI;
  - existen integraciones para archivos válidos y errores obligatorios del MVP;
  - el smoke test con Ollama real es explícito, pequeño y separado del resto de la suite.
- **Validación mínima**: ejecutar la suite mínima definida para unitarios e integración y correr el smoke test previsto para Ollama real.
