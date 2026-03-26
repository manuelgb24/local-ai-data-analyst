# PROJECT_BRIEF

## Objetivo del proyecto
Construir un MVP local-first que permita ejecutar un agente de análisis sobre un dataset externo entregado como archivo local, obtener respuestas útiles en lenguaje natural y dejar una base preparada para crecer sin rehacer la arquitectura.

## Problema que resuelve
Hoy, analizar archivos de datos externos suele exigir demasiados pasos manuales, herramientas dispersas y poca trazabilidad. Los analistas de datos todavía pierden tiempo cargando archivos, inspeccionando esquemas, limpiando contexto, lanzando consultas, generando visualizaciones y redactando conclusiones por separado.

`3_agents` nace para reducir al máximo ese trabajo manual usando la capacidad de razonamiento de un modelo local. La idea no es solo analizar datos, sino automatizar el flujo completo de análisis de forma controlada: elegir un agente, pasar una ruta local, formular una pregunta y recibir un análisis consistente, trazable y ejecutado íntegramente en local.

## Usuario y flujo principal
Usuario inicial:
- persona técnica o semitécnica que descarga un dataset y quiere analizarlo con ayuda de un agente;
- trabaja en local y quiere control explícito sobre el archivo y el agente ejecutado.

Flujo principal:
1. el usuario selecciona el agente;
2. indica la ruta local del dataset;
3. formula la pregunta;
4. el sistema prepara el dataset en DuckDB;
5. el agente analiza y devuelve una salida estructurada y trazable.

## Alcance del MVP
- Un único agente real: `data_analyst`.
- Selección explícita de agente.
- Un dataset principal por run.
- Archivos locales como fuente de entrada: `csv`, `xlsx`, `parquet`.
- DuckDB como único motor de datos.
- DeepSeek-R1:8b vía Ollama como modelo fijo del agente.
- CLI como única interfaz de ejecución inicial.
- Trazabilidad básica por sesión y run.
- Salida estructurada con narrativa, hallazgos y referencias a artefactos.

## No-objetivos
No forman parte de este MVP:
- frontend;
- API;
- Planner;
- routing automático;
- multi-agent real;
- RAG;
- multi-dataset por run;
- catálogo avanzado de datasets;
- autenticación, colas o infraestructura distribuida.

## Restricciones
- Local-first.
- Alcance pequeño y controlado.
- Sin sobreingeniería.
- Sin dependencias nuevas sin justificación clara.
- El modelo del agente es fijo en esta fase.
- El core debe quedar reutilizable por futuras interfaces sin duplicar lógica.

## Entregable real del vertical slice MVP
Un flujo completo en CLI donde el usuario pueda ejecutar `data_analyst` sobre un archivo local real, recibir un análisis útil y reproducible, y disponer de trazabilidad mínima del run y de los outputs generados.
