# AGENTS.md

## Misión actual del proyecto
`3_agents` tiene el **MVP local-first cerrado** y validado. Ese MVP deja de tratarse como trabajo pendiente y pasa a ser la base estable del producto.

La misión actual es evolucionar ese core hacia un producto **usable, operable y distribuible** sin rehacer la arquitectura ni abrir alcance innecesario.

El producto objetivo de esta etapa es:
- **local-first**;
- **monorepo único**;
- **interfaz web principal**;
- **API local** encima del core existente;
- **CLI mantenida** como interfaz operativa/técnica.

## Estado actual reconocido
El repositorio ya dispone de:
- un único agente real: `data_analyst`;
- ejecución por CLI de extremo a extremo;
- carga local de `csv`, `xlsx` y `parquet`;
- análisis sobre DuckDB local;
- integración con `deepseek-r1:8b` vía Ollama;
- generación de artifacts y trazabilidad básica;
- cobertura mínima de tests unitarios, integración, E2E y smoke.

La documentación y las siguientes tareas deben asumir ese punto de partida y no hablar del MVP como si siguiera pendiente de construcción.

## Guardrails permanentes del producto
Estas reglas siguen vigentes aunque el proyecto entre en fase producto:
- **Planner prohibido**.
- **Routing automático prohibido**.
- **Multi-agent real prohibido por ahora**.
- No abrir backend hosted, auth o multiusuario antes de una decisión formal.
- No romper la separación entre interfaz, aplicación, runtime, agente, datos, artifacts y adapters.
- No mezclar documentación estratégica con implementación de producto en la misma tarea si no hace falta.

## Alcance funcional congelado de la siguiente etapa
Hasta nueva decisión formal, el producto sigue operando con:
- un único agente real: `data_analyst`;
- selección explícita del agente;
- un único dataset principal por run;
- entrada por ruta manual local a archivo (`csv`, `xlsx`, `parquet`);
- DuckDB local como único motor de datos;
- `deepseek-r1:8b` vía Ollama como modelo fijo;
- artifacts trazables por run.

La siguiente etapa cambia **la superficie del producto**, no el núcleo funcional.

## Arquitectura permitida en esta fase
Ruta principal permitida del producto:

`interfaces/web -> interfaces/api -> application -> runtime -> agents/data_analyst -> data / artifacts / adapters`

Ruta operativa que se mantiene:

`interfaces/cli -> application -> runtime -> agents/data_analyst -> data / artifacts / adapters`

Reglas arquitectónicas:
- `interfaces/web` expone la experiencia principal del usuario.
- `interfaces/api` publica contratos locales para lanzar runs, consultar estado, listar runs y revisar artifacts.
- `interfaces/cli` queda como interfaz operativa, de soporte y validación manual.
- `application` mantiene los casos de uso.
- `runtime` coordina la ejecución del run.
- `Agent Registry` solo resuelve `agent_id` a implementación/configuración estática.
- `data_analyst` concentra la inteligencia analítica del producto.
- `data` prepara y expone el dataset local.
- `artifacts` persiste outputs trazables.
- `adapters` encapsula dependencias externas como DuckDB y Ollama.
- `observability` debe crecer para cubrir operación local, health y diagnóstico.
- `docs/TASKS.md` es la secuencia operativa principal para las fases futuras del producto.

## Límites actuales del sistema
Siguen fuera de alcance por ahora:
- backend hosted;
- auth;
- multiusuario;
- colas, jobs distribuidos o workers remotos;
- RAG;
- catálogo complejo de datasets;
- multi-agent real;
- multi-dataset por run;
- auto-selección de agente.

## Reglas de trabajo del repo
- Documentation-first antes de reabrir implementación relevante.
- Cambios pequeños, acotados y verificables.
- No introducir dependencias nuevas sin justificar su necesidad.
- No reintroducir Planner ni routing automático.
- No implementar features fuera de scope.
- Mantener separación clara entre capas.
- Actualizar documentación cuando cambie una decisión importante.
- Mantener coherencia entre `docs/TASKS.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/CONTRACTS.md` y `docs/PRODUCT_SCOPE.md`.

## Definition of Done
Una tarea se considera terminada solo si:
- respeta el alcance funcional vigente;
- mantiene la separación de capas;
- deja cambios revisables y entendibles;
- actualiza documentación si cambia una decisión o comportamiento;
- añade o ajusta validaciones/tests cuando aplica;
- no introduce piezas futuras fuera de scope;
- deja claro si el cambio pertenece al core, a la API local, a la UI o a la operación.

## Validaciones mínimas antes de cerrar una tarea
- Revisar el cambio contra `docs/TASKS.md` y `docs/PRODUCT_SCOPE.md`.
- Comprobar que no se abrió alcance accidentalmente.
- Comprobar que no se reintrodujeron Planner, routing automático o multi-agent real.
- Verificar consistencia con `docs/ARCHITECTURE.md`, `docs/DECISIONS.md` y `docs/CONTRACTS.md`.
- Verificar el resultado real antes de afirmar que está cerrado.

## Implementación permitida en la siguiente fase
### Qué sí se puede implementar ahora
- readiness, health y UX operativa local.
- API local mínima reutilizando el core existente.
- UI web local usando ruta manual de dataset.
- historial persistente local de runs y exploración de artifacts.
- observabilidad mínima del producto.
- packaging y distribución local del producto.
- CI y release hardening.

### Qué sigue fuera de alcance
- Planner.
- Routing automático.
- Backend hosted.
- Multi-agent real.
- Multi-dataset por run.
- Auth.
- RAG.
- Colas, jobs distribuidos o workers remotos.
- Catálogo complejo de datasets.

## Sobreingeniería que no debe introducirse
- Abstracciones para futuros agentes que todavía no existen.
- Configuración prematura de múltiples modelos, proveedores o backends remotos.
- Plugin frameworks, registries complejos u orquestadores adicionales.
- Capas nuevas sin una responsabilidad clara dentro de la arquitectura permitida.
- Features “por si acaso” fuera del alcance funcional fijado.

## Cómo trabajar en este repo
- Toma el core actual como base, no como borrador.
- Haz cambios pequeños, concretos y verificables.
- Toca solo las piezas necesarias para el objetivo actual.
- Usa `docs/TASKS.md` como guía secuencial principal de trabajo futuro.
- Valida el resultado real antes de cerrar una tarea.
- No inventes arquitectura nueva ni reabras decisiones ya congeladas sin documentarlo.
