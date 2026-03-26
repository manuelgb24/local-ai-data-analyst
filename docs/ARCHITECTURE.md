# ARCHITECTURE

## Visión general
La arquitectura del MVP se centra en una ejecución simple y controlada: el usuario elige un agente, entrega una ruta local a un dataset y formula una pregunta. El sistema crea o recupera contexto de sesión, registra un run, prepara el dataset en DuckDB, resuelve el agente mediante un `Agent Registry` ligero y ejecuta el análisis.

No existe Planner. No existe routing automático. La inteligencia del MVP está concentrada en un único agente real: `data_analyst`.

## Capas del sistema y responsabilidades

### 1. `interfaces/cli`
- Recoge la entrada del usuario.
- Expone la selección explícita del agente.
- Muestra la respuesta final y referencias a outputs.

### 2. `application`
- Contiene el caso de uso principal de ejecución.
- Orquesta el flujo sin implementar detalles de infraestructura.
- Traduce la petición externa al flujo interno del sistema.

### 3. `runtime`
- Crea o recupera sesión.
- Crea el run.
- Valida la solicitud inicial.
- Resuelve el agente mediante el `Agent Registry`.
- Coordina la preparación del dataset y la ejecución del agente.

### 4. `agents/data_analyst`
- Recibe un contexto estructurado.
- Analiza el dataset cargado en DuckDB.
- Devuelve una salida estructurada, no una respuesta ligada a la CLI.

### 5. `data`
- Valida la ruta y el formato del archivo.
- Carga el dataset local.
- Genera metadata mínima del dataset.
- Lo deja disponible para consulta local en DuckDB.

### 6. `artifacts`
- Define el manifiesto de outputs del run.
- Organiza tablas, gráficos y respuesta generada como salidas trazables.

### 7. `adapters`
- Aíslan integraciones concretas con Ollama, DuckDB y almacenamiento local.
- Evitan acoplar dependencias externas al core.

### 8. `observability`
- Proporciona logging, errores tipados y trazabilidad mínima por `session_id` y `run_id`.

## Flujo end-to-end de una ejecución
1. La CLI recibe `agent_id`, `dataset_path`, `user_prompt` y opcionalmente `session_id`.
2. `application` invoca el caso de uso principal.
3. `runtime` valida la petición inicial.
4. `runtime` crea o recupera la sesión y abre un nuevo run.
5. `runtime` usa `Agent Registry` para resolver el agente solicitado.
6. `data` valida el archivo, detecta formato, lo carga en DuckDB y genera metadata básica.
7. `runtime` construye el contexto estructurado de ejecución.
8. `data_analyst` usa ese contexto para analizar y producir una salida estructurada.
9. `artifacts` registra los outputs del run.
10. La CLI renderiza la salida final para el usuario.

## Papel del runtime
El `runtime` es la pieza central de ejecución del MVP. Su papel es:
- recibir la solicitud ya parseada;
- gestionar sesión y run;
- coordinar la preparación del dataset;
- resolver el agente correcto;
- invocar al agente y devolver su resultado.

El `runtime` **no** decide estrategia de negocio ni interpreta intención para escoger un agente automáticamente.

## Papel del Agent Registry
El `Agent Registry` existe para permitir escalabilidad futura sin complicar el MVP.

Su responsabilidad en esta fase es solo:
- aceptar un `agent_id`;
- resolverlo a una implementación disponible;
- exponer configuración estática mínima asociada al agente.

El `Agent Registry` **no**:
- piensa;
- enruta;
- reescribe prompts;
- decide qué agente conviene;
- actúa como Planner encubierto.

## Límites del MVP
- Un solo agente real: `data_analyst`.
- Un único dataset por run.
- Solo archivos locales soportados.
- Solo DuckDB como motor.
- Solo CLI como interfaz.
- Sin multi-agent real.
- Sin API, frontend, auth, colas, RAG ni catálogo avanzado.

## Crecimiento futuro permitido
Sin comprometer la implementación actual, esta arquitectura permite:
- añadir nuevos agentes detrás del `Agent Registry`;
- incorporar nuevas interfaces encima del mismo core;
- introducir configuraciones específicas por agente;
- ampliar el catálogo de adapters si el producto lo exige.

Ese crecimiento futuro debe ocurrir sin romper tres reglas:
- mantener selección explícita del agente mientras el producto siga simple;
- no mezclar ejecución con routing inteligente sin una decisión nueva formal;
- no degradar la separación entre core, adapters e interfaces.
