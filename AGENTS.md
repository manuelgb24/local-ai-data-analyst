# AGENTS.md

## Misión real del proyecto
`3_agents` construye un sistema **local-first** para analizar datasets externos desde archivos locales usando un agente especializado. El objetivo no es una demo rápida: es dejar una base limpia, mantenible y ampliable para evolucionar después hacia un producto serio sin rehacer el core.

## Alcance congelado del MVP
- Un único agente real: `data_analyst`.
- Selección explícita del agente por parte del usuario.
- Un único dataset principal por run.
- Entrada desde archivo local (`csv`, `xlsx`, `parquet`).
- Carga y consulta local en DuckDB.
- Modelo fijo: DeepSeek-R1:8b vía Ollama.
- CLI primero.
- Salida estructurada y trazable.

## Arquitectura permitida
Ruta principal permitida para el MVP:

`interfaces/cli -> application -> runtime -> agents/data_analyst -> data / artifacts / adapters`

Reglas arquitectónicas:
- `runtime` coordina la ejecución del run.
- `Agent Registry` solo resuelve `agent_id` a implementación/configuración estática.
- `data_analyst` hace el análisis.
- `data` prepara y expone el dataset.
- `artifacts` define outputs y manifest.
- `adapters` encapsula dependencias externas como Ollama y DuckDB.
- **Planner prohibido**.
- **Routing automático prohibido**.

## Límites claros del sistema
Fuera del MVP:
- API.
- Frontend.
- Auth.
- Colas, jobs distribuidos o workers remotos.
- RAG.
- Catálogo complejo de datasets.
- Multi-agent real.
- Multi-dataset por run.
- Auto-selección de agente.

## Reglas de trabajo del repo
- Plan first, code later.
- Cambios pequeños, acotados y verificables.
- No introducir dependencias nuevas sin justificar su necesidad.
- No reintroducir Planner ni routing automático.
- No implementar features fuera de scope.
- Mantener separación clara entre capas.
- Actualizar documentación cuando cambie una decisión importante.
- No mezclar documentación estratégica con lógica de producto en la misma tarea.

## Definition of Done
Una tarea se considera terminada solo si:
- respeta el alcance congelado del MVP;
- mantiene la separación de capas;
- deja los cambios revisables y entendibles;
- actualiza documentación si la decisión o el comportamiento cambió;
- añade o ajusta validaciones/tests cuando aplique;
- no introduce piezas futuras fuera de scope.

## Validaciones mínimas antes de cerrar una tarea
- Revisar el cambio contra el plan vigente del MVP.
- Comprobar que no se abrió alcance accidentalmente.
- Comprobar que no se reintrodujeron Planner, routing automático o multi-agent real.
- Verificar consistencia con `docs/ARCHITECTURE.md`, `docs/DECISIONS.md` y `docs/CONTRACTS.md`.
- Verificar el resultado real antes de afirmar que está cerrado.

## Implementación permitida en esta fase
### Qué sí se puede implementar ahora dentro del MVP
- Runtime real del run dentro de la arquitectura ya aprobada.
- Loaders de datos para `csv`, `xlsx` y `parquet`.
- Implementación real del agente `data_analyst`.
- CLI ejecutable para lanzar el flujo completo.
- Generación real de artefactos y `ArtifactManifest`.
- Adapters mínimos y concretos para DuckDB y Ollama.
- Validaciones y tests necesarios para cerrar el vertical slice.

### Qué sigue fuera de alcance
- Planner.
- Routing automático.
- Frontend.
- API.
- RAG.
- Multi-agent real.
- Multi-dataset por run.
- Auth.
- Colas, jobs distribuidos o workers remotos.
- Catálogo complejo de datasets.
- MCP específico del proyecto.
- Skills o subagentes propios del proyecto que no sean imprescindibles para cerrar este vertical slice.

### Sobreingeniería que no debe introducirse
- Abstracciones para futuros agentes que el MVP todavía no necesita.
- Configuración prematura de múltiples modelos, proveedores o backends.
- Plugin frameworks, registries complejos u orquestadores adicionales.
- Capas nuevas sin una responsabilidad clara dentro de la arquitectura permitida.
- Features "por si acaso" fuera del alcance congelado.

## Cómo trabajar en este repo
- Haz cambios pequeños, concretos y verificables.
- Toca solo las piezas necesarias para el objetivo actual.
- Valida el resultado real antes de cerrar una tarea.
- No inventes arquitectura nueva ni reabras decisiones ya congeladas.
