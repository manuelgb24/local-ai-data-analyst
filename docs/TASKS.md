# TASKS

## Propósito
El MVP está cerrado.

Este documento guía la etapa posterior al MVP y es la **fuente operativa principal** para el trabajo futuro del proyecto. Cuando haya que decidir qué sigue y en qué orden, la referencia canónica es este archivo.

## Cómo usar este documento
- Ejecutar las fases en orden.
- No abrir trabajo de una fase posterior sin cerrar la anterior o documentar por qué se adelanta.
- Si una fase obliga a cambiar contratos, arquitectura, alcance o decisiones, actualizar primero la documentación fuente de verdad correspondiente.
- Usar este archivo como referencia principal cuando falte memoria contextual de sesiones anteriores.

## Skills relevantes para este roadmap
Este documento solo lista las skills que tienen encaje directo con el roadmap actual de `3_agents`. Las skills instaladas sin relación real con estas fases quedan fuera de `docs/TASKS.md` para no introducir ruido operativo.

### Skills transversales
- `brainstorming` — explorar intención, alcance y decisiones de una fase antes de inventar comportamiento nuevo.
- `writing-plans` — convertir una fase o bloque relevante en un plan ejecutable antes de tocar implementación importante.
- `systematic-debugging` — investigar bugs, tests rotos o comportamientos inesperados antes de proponer arreglos.
- `requesting-code-review` — pedir revisión antes de cerrar cambios importantes o preparar merge/release.
- `verification-before-completion` — exigir evidencia fresca antes de afirmar que una tarea o fase está realmente cerrada.

### Skills específicas por tipo de trabajo
- `architecture-patterns` — definir boundaries, separación de capas, persistencia y contratos sin romper la arquitectura permitida.
- `python-testing-patterns` — diseñar y ampliar tests Python para core, API, persistencia, operación y checks automatizados.
- `python-observability` — añadir logs estructurados, correlación, health, readiness y diagnóstico operativo.
- `playwright` — automatizar browser E2E y validar flujos reales de la futura UI local.
- `vercel-react-best-practices` — implementar o refactorizar UI React/Next con buenas prácticas de rendimiento y estructura.
- `vercel-composition-patterns` — diseñar composición de componentes, formularios y APIs de UI escalables.
- `web-design-guidelines` — revisar UX, accesibilidad y calidad de interfaz cuando la UI ya exista.

---

## Fase 1 — Readiness, configuración y UX operativa local
- **Objetivo**: hacer visible y accionable el estado operativo del sistema antes de lanzar un run.
- **Por qué va primero**: la futura API local y la futura UI principal dependen de un estado operativo claro del producto y del proveedor local.
- **Dependencias**: ninguna; es la primera fase post-MVP.
- **Incluye**:
  - health de aplicación;
  - health del proveedor local;
  - mensajes accionables cuando falte Ollama o el modelo;
  - configuración mínima legible por API/UI;
  - base documental para distinguir sistema listo vs sistema no listo.
- **Criterios de aceptación**:
  - el usuario puede saber si el sistema está listo antes de lanzar un run;
  - la documentación describe con claridad el estado operativo esperado;
  - la semántica de readiness no depende de auto-start ni de comportamiento implícito.
- **Validación mínima**:
  - verificación del estado del proveedor local;
  - coherencia entre mensajes operativos, `docs/OPERATIONS.md` y `docs/TEST_PLAN.md`.
### Skills aplicables en esta fase
| Subtrabajo | Skill principal | Skills de apoyo | Cuándo usarla |
| --- | --- | --- | --- |
| Readiness, health y diagnóstico local | `python-observability` | `architecture-patterns` | Al definir cómo se expone el estado operativo y cómo se distingue sistema listo vs no listo. |
| Boundaries de health, config y superficies operativas | `architecture-patterns` | `python-observability` | Al fijar responsabilidades entre interfaces, core y adapters sin romper capas. |
| Tests de readiness, errores operativos y coherencia técnica | `python-testing-patterns` | `verification-before-completion` | Al validar checks operativos, mensajes accionables y consistencia con la documentación. |

## Fase 2 — API local mínima
- **Objetivo**: publicar una API local estable reutilizando el core actual.
- **Por qué va segunda**: la interfaz principal y el historial persistente necesitan una superficie local estable antes de crecer.
- **Dependencias**:
  - Fase 1 completada.
- **Incluye**:
  - `POST /runs`;
  - `GET /runs`;
  - `GET /runs/{run_id}`;
  - `GET /runs/{run_id}/artifacts`;
  - `GET /health`;
  - `GET /health/proveedor`;
  - traducción consistente de errores del core a errores de API.
- **Criterios de aceptación**:
  - la API local reutiliza `application` y `runtime` sin duplicar lógica;
  - acepta `dataset_path` manual como contrato de entrada;
  - expone un contrato mínimo consistente para runs, artifacts y health.
- **Validación mínima**:
  - contract tests de endpoints mínimos;
  - integración API + core;
  - verificación de errores de validación y del proveedor local.
### Skills aplicables en esta fase
| Subtrabajo | Skill principal | Skills de apoyo | Cuándo usarla |
| --- | --- | --- | --- |
| Diseño de endpoints, contratos y separación por capas | `architecture-patterns` | `writing-plans` | Al decidir cómo exponer la API local reutilizando `application` y `runtime` sin duplicar lógica. |
| Contract tests e integración API + core | `python-testing-patterns` | `architecture-patterns` | Al comprobar request/response, mapeo de errores y consistencia de los endpoints mínimos. |
| Fallos de integración o mapeo de errores | `systematic-debugging` | `python-testing-patterns` | Al investigar comportamientos inesperados entre API, core y proveedor local. |

## Fase 3 — Interfaz principal con ruta manual de dataset
- **Objetivo**: añadir una UI local para lanzar y revisar runs usando ruta manual local al dataset.
- **Por qué va tercera**: necesita la API local ya definida y no debe inventar contratos propios.
- **Dependencias**:
  - Fase 2 completada.
- **Incluye**:
  - pantalla de readiness;
  - formulario principal;
  - entrada por ruta manual local al dataset;
  - visualización de narrativa, hallazgos y artifacts;
  - tratamiento claro de errores operativos.
- **Criterios de aceptación**:
  - un usuario puede completar el flujo principal sin pasar por CLI;
  - la UI no introduce semántica distinta de la ya fijada por `dataset_path`;
  - los errores operativos son comprensibles.
- **Validación mínima**:
  - browser E2E del flujo con ruta manual de dataset;
  - comprobación de que la UI consume solo contratos documentados de la API.
### Skills aplicables en esta fase
| Subtrabajo | Skill principal | Skills de apoyo | Cuándo usarla |
| --- | --- | --- | --- |
| Implementación o refactor de UI React | `vercel-react-best-practices` | `writing-plans` | Al construir la interfaz principal sin degradar rendimiento ni crear patterns pobres de UI. |
| Estructura de componentes, formularios y composición | `vercel-composition-patterns` | `vercel-react-best-practices` | Al diseñar la API interna de componentes y evitar props/flows difíciles de mantener. |
| Browser E2E del flujo principal | `playwright` | `verification-before-completion` | Al validar el recorrido real desde readiness hasta visualización del resultado. |
| Auditoría UX y accesibilidad de la UI construida | `web-design-guidelines` | `playwright` | Al revisar la experiencia final y detectar problemas de interfaz visibles. |

## Fase 4 — Historial persistente de runs y artifacts
- **Objetivo**: hacer la trazabilidad del producto realmente reutilizable fuera del proceso actual.
- **Por qué va cuarta**: una vez hay API y UI mínimas, el siguiente salto útil es poder consultar ejecuciones previas de forma persistente.
- **Nota de implementación ya consolidada**: la base file-backed (`run.json` junto a artifacts) y los endpoints `GET /runs*` se adelantaron en Fase 2 para mantener contratos y documentación alineados; esta fase cierra la exposición web del historial y su hardening.
- **Dependencias**:
  - Fase 2 completada;
  - preferiblemente Fase 3 iniciada o completada para aprovechar la visualización.
- **Incluye**:
  - persistencia local file-backed de metadata de runs;
  - listado de runs persistidos;
  - detalle de run persistido;
  - acceso simple a artifacts persistidos;
  - coherencia entre metadata de run y artifacts existentes.
- **Criterios de aceptación**:
  - `GET /runs` devuelve historial local persistente;
  - `GET /runs/{run_id}` no depende solo del proceso actual;
  - la UI o la operación local pueden consultar runs previos.
- **Validación mínima**:
  - escenarios de persistencia local;
  - listados de runs;
  - disponibilidad del historial tras reinicio del proceso cuando la metadata persistida existe.
### Skills aplicables en esta fase
| Subtrabajo | Skill principal | Skills de apoyo | Cuándo usarla |
| --- | --- | --- | --- |
| Diseño file-backed, boundaries y consistencia con artifacts | `architecture-patterns` | `writing-plans` | Al definir la persistencia local mínima sin introducir una base adicional ni romper el core. |
| Tests de persistencia, listados y reinicio de proceso | `python-testing-patterns` | `verification-before-completion` | Al probar historial, detalle de runs y coherencia tras reinicios. |
| Diagnóstico de inconsistencias metadata/artifacts | `systematic-debugging` | `python-testing-patterns` | Al investigar runs persistidos incompletos, metadata ausente o artifacts faltantes. |

## Fase 5 — Observabilidad del producto
- **Objetivo**: mejorar diagnóstico, soporte y operación local.
- **Por qué va quinta**: una vez existen API, UI y persistencia local, la trazabilidad operativa se vuelve más importante.
- **Dependencias**:
  - Fases 1 a 4 al menos parcialmente resueltas.
- **Incluye**:
  - logs estructurados;
  - correlación por `session_id` y `run_id`;
  - visibilidad clara de health y errores;
  - criterios mínimos de soporte operativo.
- **Criterios de aceptación**:
  - errores y estados del sistema son trazables sin inspección manual caótica;
  - la operación local distingue con claridad error del core, del dataset y del proveedor.
- **Validación mínima**:
  - comprobación documental y técnica de correlación básica;
  - consistencia entre health, logs y errores expuestos.
### Skills aplicables en esta fase
| Subtrabajo | Skill principal | Skills de apoyo | Cuándo usarla |
| --- | --- | --- | --- |
| Logs estructurados, correlación y health visible | `python-observability` | `architecture-patterns` | Al instrumentar el sistema para soporte y diagnóstico sin mezclar lógica transversal con interfaz. |
| Encaje transversal sin romper capas | `architecture-patterns` | `python-observability` | Al fijar dónde vive la observabilidad dentro de la arquitectura permitida. |
| Validación técnica de correlación y errores expuestos | `python-testing-patterns` | `verification-before-completion` | Al comprobar que logs, health y errores son consistentes y trazables. |

## Fase 6 — Packaging y distribución local
- **Objetivo**: convertir el sistema en algo instalable y arrancable con fricción reducida.
- **Por qué va sexta**: antes de endurecer release final, hace falta una historia clara de instalación y arranque.
- **Dependencias**:
  - Fases 1 a 5 suficientemente maduras.
- **Incluye**:
  - estrategia de arranque local reproducible;
  - documentación de instalación;
  - validaciones previas a release;
  - artefactos de distribución si se aprueban.
- **Criterios de aceptación**:
  - existe una historia clara de instalación y uso local;
  - la forma de distribuir el producto no contradice el modelo local-first.
- **Validación mínima**:
  - verificación de arranque reproducible;
  - coherencia entre empaquetado previsto y `docs/OPERATIONS.md`.
### Skills aplicables en esta fase
| Subtrabajo | Skill principal | Skills de apoyo | Cuándo usarla |
| --- | --- | --- | --- |
| Planificación de packaging y distribución local | `writing-plans` | `architecture-patterns` | Al descomponer el trabajo de instalación, arranque y distribución en pasos concretos y verificables. |
| Validaciones reproducibles de instalación y arranque | `python-testing-patterns` | `verification-before-completion` | Al automatizar o documentar checks de setup y arranque local repetible. |
| Cierre con evidencia real de uso y arranque | `verification-before-completion` | `python-testing-patterns` | Antes de afirmar que la distribución local es usable. |
| Nota de alcance sobre skills | _No hay skill instalada especializada en packaging_ | `writing-plans` | Tenerlo explícito para no forzar una skill que no existe para este tipo de trabajo. |

## Fase 7 — CI y release hardening
- **Objetivo**: formalizar la validación previa a publicar una versión usable.
- **Por qué va séptima**: es la fase de consolidación final, cuando ya existe superficie suficiente para automatizar checks con sentido.
- **Dependencias**:
  - Fases 1 a 6 suficientemente maduras.
- **Incluye**:
  - ejecución automatizada de checks;
  - cobertura de tests de core, API y UI;
  - criterios de release;
  - smoke manual/real documentado.
- **Criterios de aceptación**:
  - publicar una versión ya no depende de memoria informal o pasos implícitos;
  - la checklist de release es defendible y repetible.
- **Validación mínima**:
  - verificación de la suite consolidada aplicable;
  - revisión de coherencia entre release, operación y alcance.
### Skills aplicables en esta fase
| Subtrabajo | Skill principal | Skills de apoyo | Cuándo usarla |
| --- | --- | --- | --- |
| Automatización de checks y suites | `python-testing-patterns` | `writing-plans` | Al consolidar la validación de core, API y operación en pipelines repetibles. |
| Lane de UI/browser cuando exista interfaz | `playwright` | `python-testing-patterns` | Al incorporar validación E2E real de la interfaz principal dentro del endurecimiento de release. |
| Verificación previa a afirmar “release lista” | `verification-before-completion` | `python-testing-patterns` | Antes de declarar que una versión está preparada para publicarse. |
| Revisión final antes de merge o release | `requesting-code-review` | `verification-before-completion` | Al cerrar un bloque importante o preparar una versión utilizable. |

---

## Reglas de uso de este documento
- Este archivo manda sobre la secuencia futura de trabajo.
- No añadir aquí detalle de implementación de bajo nivel; ese nivel vive en planes específicos.
- Si una fase cambia arquitectura, contratos, operación, tests, release o alcance en el transcurso de las implementaciones, actualizar primero la documentación fuente de verdad correspondiente.
- No abrir features fuera de `docs/PRODUCT_SCOPE.md`.

## Uso transversal de skills
- Antes de abrir implementación relevante de una fase, usar `brainstorming` si hay diseño nuevo y `writing-plans` si el trabajo es multi-step.
- Si aparece un bug, un test roto o un comportamiento inesperado, usar `systematic-debugging` antes de proponer arreglos.
- Antes de cerrar una tarea o fase, aplicar `verification-before-completion`.
- Antes de merge o al cerrar un bloque importante, usar `requesting-code-review`.
