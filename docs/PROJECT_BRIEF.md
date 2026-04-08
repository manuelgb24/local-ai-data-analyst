# PROJECT_BRIEF

## Objetivo del producto
Convertir el MVP local-first ya implementado en un **producto usable** que permita a una persona técnica o semitécnica analizar datasets locales mediante una experiencia más accesible, sin perder control explícito sobre el archivo, el agente, los artifacts y la ejecución local.

La siguiente fase no persigue “volver a construir el MVP”, sino **llevarlo a un formato de producto** con:
- interfaz web principal;
- API local;
- CLI mantenida para soporte operativo;
- operación local clara y diagnósticos reproducibles.

## Problema que resuelve
Analizar datasets externos sigue requiriendo demasiadas herramientas, demasiados pasos manuales y muy poca trazabilidad. El MVP ya demostró que `3_agents` puede reducir esa fricción. La etapa producto debe resolver ahora otro problema: **hacer esa capacidad utilizable, entendible y operable fuera de una demo técnica por CLI**.

## Usuario objetivo
Usuario inicial del producto:
- persona técnica o semitécnica;
- trabaja en local y quiere control explícito sobre el archivo y el análisis;
- necesita una forma simple de lanzar un run, revisar resultados y localizar artifacts;
- no quiere depender de un backend remoto para la capacidad principal del sistema.

## Experiencia objetivo
Flujo principal deseado en la siguiente etapa:
1. el usuario abre la interfaz web local;
2. verifica que el sistema y Ollama están listos;
3. selecciona el agente disponible;
4. indica una ruta manual local al dataset;
5. formula la pregunta;
6. el sistema prepara el dataset en DuckDB;
7. el agente ejecuta el análisis;
8. el usuario revisa narrativa, hallazgos, artifacts y estado del run.

La CLI seguirá permitiendo:
- validación manual;
- soporte técnico;
- smoke tests;
- operación avanzada o scripting local.

## Alcance funcional vigente
La fase producto mantiene congelado el núcleo funcional actual:
- un único agente real: `data_analyst`;
- selección explícita del agente;
- un dataset principal por run;
- archivos locales como fuente de entrada mediante ruta manual: `csv`, `xlsx`, `parquet`;
- DuckDB como único motor de datos;
- `deepseek-r1:8b` vía Ollama como modelo fijo;
- salida estructurada y trazable con artifacts.

## No-objetivos actuales
No forman parte de esta etapa:
- backend hosted;
- auth;
- multiusuario;
- Planner;
- routing automático;
- multi-agent real;
- RAG;
- varios datasets por run;
- catálogo avanzado de datasets;
- infraestructura distribuida.

## Restricciones activas
- Local-first como decisión de producto.
- Monorepo único.
- Sin sobreingeniería.
- Sin dependencias nuevas sin justificación clara.
- El core actual debe seguir siendo reutilizable por CLI, API y UI.
- La UI y la API no deben duplicar lógica que hoy vive en `application` y `runtime`.
- La entrada documentada del dataset sigue siendo una ruta manual local, coherente con el patrón actual del repositorio.

## Resultado esperado de la siguiente fase
Un producto local-first en el que:
- el core actual siga intacto como base;
- exista una API local mínima;
- exista una interfaz web principal usable;
- el estado operativo del proveedor local sea visible;
- exista historial persistente local de runs;
- los runs y artifacts sean más fáciles de revisar;
- la operación y la distribución local sean más claras.
