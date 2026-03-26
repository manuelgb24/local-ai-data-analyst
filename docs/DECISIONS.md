# DECISIONS

## D-001 — No habrá Planner en el MVP
- **Decisión**: eliminar la figura del Planner.
- **Motivo**: para este MVP añade complejidad innecesaria y riesgo de duplicar razonamiento sin aportar valor real.
- **Impacto**: la selección del agente queda en manos del usuario y el core se simplifica.
- **Descartes**: mantener Planner como jefe o usar routing automático.
- **Estado**: aceptada.

## D-002 — La selección del agente es explícita
- **Decisión**: el usuario indica qué agente quiere ejecutar.
- **Motivo**: el producto empieza con pocos agentes y el control explícito evita ambigüedad.
- **Impacto**: la interfaz debe pedir `agent_id` y el sistema no decide por sí solo.
- **Descartes**: clasificación automática de intención o auto-routing.
- **Estado**: aceptada.

## D-003 — El Agent Registry será ligero
- **Decisión**: mantener un `Agent Registry` como resolución ligera de `agent_id`.
- **Motivo**: deja preparada la escalabilidad futura sin inflar el MVP.
- **Impacto**: el runtime puede crecer a más agentes sin cambiar la estructura general.
- **Descartes**: wiring rígido para siempre o registry complejo tipo plugin framework.
- **Estado**: aceptada.

## D-004 — El modelo del agente será DeepSeek vía Ollama
- **Decisión**: usar DeepSeek-R1:8b a través de Ollama como modelo fijo del agente del MVP.
- **Motivo**: reduce ambigüedad y mantiene consistencia de comportamiento.
- **Impacto**: no hace falta una política compleja de modelos en esta fase.
- **Descartes**: modelo configurable por ejecución o múltiples proveedores desde el inicio.
- **Estado**: aceptada.

## D-005 — La entrada del sistema será local files only
- **Decisión**: el sistema trabaja con archivos locales como entrada principal.
- **Motivo**: encaja con un enfoque local-first y evita dependencias externas innecesarias.
- **Impacto**: Kaggle puede seguir siendo fuente de descarga, pero no integración del producto.
- **Descartes**: conectores API, sincronización externa o catálogo remoto en el MVP.
- **Estado**: aceptada.

## D-006 — Cada run usa un único dataset principal
- **Decisión**: limitar el MVP a un solo dataset por run.
- **Motivo**: reduce complejidad de joins arbitrarios, trazabilidad y validación.
- **Impacto**: la capa de datos puede centrarse en una carga simple y reproducible.
- **Descartes**: múltiples datasets por petición o carpetas complejas desde el inicio.
- **Estado**: aceptada.

## D-007 — DuckDB es el único motor de datos inicial
- **Decisión**: usar DuckDB como única base/motor analítico del MVP.
- **Motivo**: simplifica el stack y cubre bien el análisis local sobre archivos.
- **Impacto**: no se introduce ninguna base adicional ni abstracción multi-backend.
- **Descartes**: SQLite, PostgreSQL o soporte multi-base preventivo.
- **Estado**: aceptada.

## D-008 — CLI first
- **Decisión**: la primera interfaz será la CLI.
- **Motivo**: permite validar el flujo real con el menor coste de implementación.
- **Impacto**: la lógica debe quedar desacoplada para que API o frontend futuros reutilicen el mismo core.
- **Descartes**: empezar por frontend o diseñar varias interfaces desde el día uno.
- **Estado**: aceptada.

## D-009 — Sin RAG ni multi-agent real en el MVP
- **Decisión**: excluir RAG y coordinación real entre varios agentes del alcance inicial.
- **Motivo**: no aportan valor directo al vertical slice actual y aumentarían mucho el alcance.
- **Impacto**: el foco queda en dataset local + análisis estructurado + salida trazable.
- **Descartes**: usar RAG como núcleo del análisis o montar colaboración entre agentes ahora.
- **Estado**: aceptada.

## D-010 — DatasetV1/Walmart_Sales.csv es solo referencia probable
- **Decisión**: tratar `DatasetV1/Walmart_Sales.csv` como dataset de referencia probable para pruebas futuras.
- **Motivo**: ayuda a preparar el vertical slice sin convertirlo en una dependencia conceptual del producto.
- **Impacto**: puede usarse más adelante en pruebas o demos, pero no define el producto.
- **Descartes**: fijarlo como dataset oficial o modelar el sistema alrededor de ese archivo.
- **Estado**: aceptada.

## D-011 — El único agente real del MVP es `data_analyst`
- **Decisión**: el MVP solo implementa un agente real, `data_analyst`.
- **Motivo**: mantiene el alcance pequeño y evita complejidad prematura en coordinación entre agentes.
- **Impacto**: el `Agent Registry` existe para escalabilidad futura, pero en esta fase solo resuelve `data_analyst`.
- **Descartes**: introducir más agentes reales o multi-agent operativo antes de cerrar el vertical slice.
- **Estado**: aceptada.
