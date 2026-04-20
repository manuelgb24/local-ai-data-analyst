# DECISIONS

## D-001 — No habrá Planner en el MVP ni en la siguiente fase
- **Decisión**: eliminar y mantener fuera la figura del Planner.
- **Motivo**: añade complejidad innecesaria y riesgo de duplicar razonamiento sin aportar valor real al producto actual.
- **Impacto**: la selección del agente sigue en manos del usuario y el core se mantiene simple.
- **Descartes**: mantener Planner como jefe o usar routing automático.
- **Estado**: aceptada.

## D-002 — La selección del agente es explícita
- **Decisión**: el usuario indica qué agente quiere ejecutar.
- **Motivo**: el producto sigue teniendo muy pocos agentes y el control explícito evita ambigüedad.
- **Impacto**: la interfaz debe pedir `agent_id` y el sistema no decide por sí solo.
- **Descartes**: clasificación automática de intención o auto-routing.
- **Estado**: aceptada.

## D-003 — El Agent Registry será ligero
- **Decisión**: mantener un `Agent Registry` como resolución ligera de `agent_id`.
- **Motivo**: deja preparada la escalabilidad futura sin inflar el producto actual.
- **Impacto**: el runtime puede crecer a más agentes sin cambiar la estructura general.
- **Descartes**: wiring rígido permanente o registry complejo tipo plugin framework.
- **Estado**: aceptada.

## D-004 — El modelo del agente será `deepseek-r1:8b` vía Ollama
- **Decisión**: usar `deepseek-r1:8b` a través de Ollama como modelo fijo.
- **Motivo**: reduce ambigüedad y mantiene consistencia de comportamiento.
- **Impacto**: no hace falta una política compleja de modelos en esta fase.
- **Descartes**: modelo configurable por ejecución o múltiples proveedores desde el inicio.
- **Estado**: aceptada.

## D-005 — La entrada del sistema será local files only
- **Decisión**: el sistema trabaja con archivos locales como entrada principal.
- **Motivo**: encaja con un enfoque local-first y evita dependencias externas innecesarias.
- **Impacto**: la experiencia de producto se diseña alrededor del archivo local, no de conectores remotos.
- **Descartes**: conectores API, sincronización externa o catálogo remoto.
- **Estado**: aceptada.

## D-006 — Cada run usa un único dataset principal
- **Decisión**: limitar el sistema actual a un solo dataset por run.
- **Motivo**: reduce complejidad de joins arbitrarios, trazabilidad y validación.
- **Impacto**: la capa de datos puede centrarse en una carga simple y reproducible.
- **Descartes**: múltiples datasets por petición o carpetas complejas.
- **Estado**: aceptada.

## D-007 — DuckDB es el único motor de datos inicial
- **Decisión**: usar DuckDB como único motor analítico del producto actual.
- **Motivo**: simplifica el stack y cubre bien el análisis local sobre archivos.
- **Impacto**: no se introduce ninguna base adicional ni abstracción multi-backend.
- **Descartes**: SQLite, PostgreSQL o soporte multi-base preventivo.
- **Estado**: aceptada.

## D-008 — CLI first para el MVP, no para el producto final
- **Decisión**: la CLI fue la primera interfaz para validar el flujo real.
- **Motivo**: permitió cerrar el vertical slice con el menor coste de implementación.
- **Impacto**: la lógica quedó desacoplada y ahora puede reutilizarse desde API y web.
- **Descartes**: empezar por frontend o varias interfaces desde el día uno.
- **Estado**: aceptada y consolidada.

## D-009 — Sin RAG ni multi-agent real
- **Decisión**: excluir RAG y coordinación real entre varios agentes del alcance actual.
- **Motivo**: no aportan valor directo al producto que estamos cerrando ahora.
- **Impacto**: el foco sigue siendo dataset local + análisis estructurado + salida trazable.
- **Descartes**: usar RAG como núcleo del análisis o montar colaboración entre agentes.
- **Estado**: aceptada.

## D-010 — `DatasetV1/Walmart_Sales.csv` es solo dataset de referencia
- **Decisión**: tratar `DatasetV1/Walmart_Sales.csv` como dataset de referencia útil para validación y demos.
- **Motivo**: ayuda a verificar el sistema sin convertirlo en dependencia conceptual del producto.
- **Impacto**: puede usarse en validaciones manuales y smoke tests, pero no define el producto.
- **Descartes**: fijarlo como dataset oficial del sistema.
- **Estado**: aceptada.

## D-011 — El único agente real actual es `data_analyst`
- **Decisión**: mantener un único agente real, `data_analyst`.
- **Motivo**: mantiene el alcance pequeño y evita complejidad prematura.
- **Impacto**: el `Agent Registry` existe para escalabilidad futura, pero solo resuelve `data_analyst`.
- **Descartes**: introducir más agentes reales antes de consolidar el producto base.
- **Estado**: aceptada.

## D-012 — El MVP está cerrado y pasa a ser la base del producto
- **Decisión**: dejar de tratar el vertical slice como trabajo pendiente y tomarlo como base estable.
- **Motivo**: el flujo core ya existe, funciona y fue validado con tests y smokes.
- **Impacto**: la documentación y el trabajo futuro pasan de “construir el MVP” a “evolucionar el producto”.
- **Descartes**: reabrir el MVP como si siguiera en fase de descubrimiento.
- **Estado**: aceptada.

## D-013 — El repositorio seguirá como monorepo único
- **Decisión**: mantener un único repositorio para core, CLI, API local, UI y documentación.
- **Motivo**: simplifica la evolución del producto local-first y evita partir prematuramente el sistema.
- **Impacto**: la documentación y arquitectura se ordenan dentro del mismo repo.
- **Descartes**: separar frontend en otro repositorio ahora.
- **Estado**: aceptada.

## D-014 — La siguiente interfaz principal será Web + API local
- **Decisión**: evolucionar el producto hacia una interfaz web principal apoyada en una API local.
- **Motivo**: hace el sistema más usable sin romper el core ya validado.
- **Impacto**: la CLI deja de ser la cara principal del producto, aunque se mantiene operativa.
- **Descartes**: seguir indefinidamente con CLI-only o saltar a un backend hosted.
- **Estado**: aceptada.

## D-015 — Local-first sigue siendo una decisión activa de producto
- **Decisión**: mantener la ejecución local como principio rector también en la siguiente fase.
- **Motivo**: forma parte del valor del producto y del diseño actual del sistema.
- **Impacto**: datasets, DuckDB y Ollama siguen siendo locales; la API es local, no remota.
- **Descartes**: mover de inmediato la capacidad principal a un backend hosted.
- **Estado**: aceptada.

## D-016 — La CLI pasa a soporte operativo y técnico
- **Decisión**: mantener la CLI, pero redefinir su papel.
- **Motivo**: sigue siendo muy útil para smoke tests, soporte, scripting y validación manual.
- **Impacto**: la experiencia principal se desplaza a web + API, mientras la CLI sigue viva como interfaz auxiliar.
- **Descartes**: eliminar la CLI o mantenerla como única interfaz del producto.
- **Estado**: aceptada.

## D-017 — Ollama sigue siendo prerequisito local explícito
- **Decisión**: mantener el requisito de Ollama levantado localmente con el modelo requerido instalado.
- **Motivo**: simplifica el producto y evita magia operativa en el adapter.
- **Impacto**: el producto debe mostrar health/readiness claros, no auto-start del proveedor.
- **Descartes**: auto-start local desde el adapter o fallback multi-proveedor.
- **Estado**: aceptada.

## D-018 — Siguen fuera de alcance auth, backend hosted y multiusuario
- **Decisión**: no abrir todavía auth, backend remoto, multiusuario ni operación distribuida.
- **Motivo**: desplazaría el proyecto a otra categoría de producto antes de consolidar la experiencia local-first.
- **Impacto**: el roadmap se centra en usabilidad, API local, operación, packaging y release.
- **Descartes**: reabrir scope enterprise antes de estabilizar el producto base.
- **Estado**: aceptada.

## D-019 — `docs/TASKS.md` es el roadmap canónico
- **Decisión**: usar `docs/TASKS.md` como única guía secuencial de trabajo futuro.
- **Motivo**: evita duplicidad documental y reduce drift cuando falte memoria contextual.
- **Impacto**: se elimina `docs/ROADMAP.md` y el resto de documentos deben referenciar `docs/TASKS.md` como fuente principal.
- **Descartes**: mantener dos roadmaps equivalentes.
- **Estado**: aceptada.

## D-020 — El roadmap post-MVP reinicia la numeración en Fase 1
- **Decisión**: no volver a listar las fases 1–10 del MVP y reiniciar la etapa posterior al MVP desde Fase 1.
- **Motivo**: el MVP ya está cerrado y la secuencia futura necesita una numeración limpia y operativa.
- **Impacto**: `docs/TASKS.md` arranca en Fase 1 post-MVP.
- **Descartes**: mezclar cronologías del MVP y post-MVP en el roadmap activo.
- **Estado**: aceptada.

## D-021 — La entrada futura documentada del dataset será por ruta manual local
- **Decisión**: mantener la entrada documentada del dataset mediante `dataset_path` o ruta manual local.
- **Motivo**: alinea la evolución futura con el uso actual del repositorio y evita ampliar semántica a subida de archivos en esta etapa.
- **Impacto**: CLI, API local y UI futura se documentan alrededor de una ruta local explícita.
- **Descartes**: subida de archivo como contrato principal en esta fase.
- **Estado**: aceptada.

## D-022 — Habrá historial persistente local de runs
- **Decisión**: documentar un historial persistente local de runs como capacidad futura aprobada.
- **Motivo**: listados y detalle de runs no deben depender solo de memoria de proceso.
- **Impacto**: se añade `GET /runs` y se fija persistencia local file-backed junto al espacio de artifacts o equivalente.
- **Descartes**: historial solo en memoria del proceso.
- **Estado**: aceptada.

## D-023 — La terminología documental se normaliza a “proveedor” y `deepseek-r1:8b`
- **Decisión**: usar “proveedor” en la prosa general y `deepseek-r1:8b` como identificador técnico del modelo.
- **Motivo**: elimina mezclas innecesarias en la documentación y mejora coherencia editorial.
- **Impacto**: contratos, arquitectura, operación, tasks y checklist deben usar esa misma convención.
- **Descartes**: alternar `provider/proveedor` o `DeepSeek-R1:8b/deepseek-r1:8b`.
- **Estado**: aceptada.

## D-024 — La Fase 5 usa logs JSON correlados solo a consola
- **Decisión**: la observabilidad mínima del producto se implementa con logs estructurados JSON emitidos a stdout/stderr, correlados por `trace_id`, `session_id` y `run_id`.
- **Motivo**: mejora soporte y diagnóstico local sin abrir persistencia adicional, rotación de logs ni trabajo de packaging fuera de alcance.
- **Impacto**: API, CLI y runtime comparten el mismo logger estructurado; la API añade `X-Trace-Id` en respuestas y los errores exponen `details.category`.
- **Descartes**: introducir `structlog`, guardar logs en archivo o adelantar observabilidad de release/distribución.
- **Estado**: aceptada.

## D-025 — La Fase 6 empaqueta el producto como runtime local monoproceso
- **Decisión**: la historia recomendada de packaging local queda en un solo proceso: la API local sirve la UI build y el producto arranca con `python -m interfaces.api --serve-web`.
- **Motivo**: reduce fricción operativa sin reabrir backend hosted, bundling adicional ni cambios en el core.
- **Impacto**: Node.js queda como dependencia de build de la UI, mientras que el runtime local publicado usa mismo origen para UI y API.
- **Descartes**: mantener dos procesos como historia principal de distribución, o generar ya zip/binario/instalador fuera del repo.
- **Estado**: aceptada.

## D-026 — La Fase 7 separa CI automatizable de smoke real de release
- **Decisión**: formalizar la validación de release en dos capas: lanes automatizables (`python` + `web`) ejecutables desde `scripts/ci_checks.py` y GitHub Actions, y gates reales/manuales (`smoke` + `python -m interfaces.api --serve-web`) fuera del CI automático.
- **Motivo**: permite endurecer CI y release sin fingir que Ollama real o el arranque monoproceso empaquetado son sustituibles por checks puramente sandboxed.
- **Impacto**: `.github/workflows/ci.yml` cubre solo `python` y `web`; `smoke` exige host preparado con Ollama + `deepseek-r1:8b`; la checklist de release y la documentación operativa distinguen ambos tipos de validación.
- **Descartes**: meter smokes reales de Ollama en el workflow CI por defecto, o tratar skips/limitaciones de entorno como “pass” para release.
- **Estado**: aceptada.

## D-027 — Los chats locales agrupan runs, no cambian el core
- **Decisión**: introducir chats persistentes locales como capa de producto sobre runs, usando `session_id = chat_id` para mantener continuidad entre preguntas del mismo dataset.
- **Motivo**: la experiencia run-centric impedía continuar una pregunta analítica; el usuario necesita 3-4 mensajes de seguimiento sobre el mismo supuesto.
- **Impacto**: la API expone `/chats*`, la UI se centra en conversación y la persistencia local guarda metadata de chat junto al espacio de artifacts.
- **Descartes**: convertir esto en Planner, routing automático, multi-agent, RAG, backend hosted o memoria global.
- **Estado**: aceptada.

## D-028 — El analista usa herramientas determinísticas acotadas antes de redactar
- **Decisión**: ampliar `data_analyst` con herramientas DuckDB determinísticas para rankings, agregaciones por grupo y correlaciones simples, sin permitir SQL libre generado por el LLM.
- **Motivo**: preguntas como “qué carrera estudia más” sí se pueden responder con el dataset; el fallo era falta de herramienta, no falta de datos.
- **Impacto**: el LLM recibe tablas derivadas y hallazgos determinísticos; la narrativa debe empezar por la conclusión cuando una herramienta responda la pregunta.
- **Descartes**: dejar que el modelo invente SQL, abrir un planner o añadir agentes especializados.
- **Estado**: aceptada.
