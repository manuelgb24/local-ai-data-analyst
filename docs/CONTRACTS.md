# CONTRACTS

## Propósito del documento
Este documento fija los contratos funcionales mínimos del MVP para que la implementación mantenga límites claros entre interfaz, runtime, capa de datos, adapters y agente. Define comportamiento esperado e interfaces mínimas; no pretende ser una especificación exhaustiva ni un contrato enterprise.

## Convenciones de lectura
- `campo`: obligatorio.
- `campo?`: opcional.
- Las colecciones pueden venir vacías cuando el contrato lo permita, pero no deben cambiar de significado entre runs.
- Todo el documento asume el MVP local-first: un solo agente real, un solo dataset principal por run, DuckDB como motor y Ollama como adapter LLM.

---

## 1. RunRequest

### Propósito
Representa la solicitud de ejecución que entra en el sistema para lanzar un run analítico.

### Campos
- `agent_id`: identificador del agente a ejecutar.
- `dataset_path`: ruta local al archivo a analizar.
- `user_prompt`: petición en lenguaje natural del usuario.
- `session_id?`: identificador opcional para continuar una sesión previa.

### Responsabilidad
Servir como punto de entrada estructurado para el flujo de ejecución del MVP.

### Invariantes y reglas mínimas
- Debe referirse a un solo dataset principal por run.
- `agent_id` debe poder resolverse en el `Agent Registry`.
- `dataset_path` debe apuntar a un archivo local, no a una URL.
- El formato esperado del archivo es `csv`, `xlsx` o `parquet`.
- `user_prompt` no puede ser vacío.

### Encaje en el flujo general
La CLI construye este contrato y lo entrega al caso de uso principal. A partir de aquí, el runtime gestiona el resto del flujo.

### Estados mínimos del run
- `created`: la solicitud fue aceptada y ya existe `run_id`.
- `preparing_dataset`: el sistema está validando, cargando o perfilando el dataset.
- `running_agent`: el dataset ya está listo y el agente está ejecutándose.
- `succeeded`: el run terminó con `AgentResult` y `ArtifactManifest` consistentes.
- `failed`: el run terminó con un error del contrato mínimo de errores.

No hace falta introducir más estados en este MVP.

---

## 2. DatasetProfile

### Propósito
Representar la metadata mínima del dataset ya validado y cargado para que el agente pueda analizarlo con contexto suficiente.

### Campos
- `source_path`: ruta original del archivo.
- `format`: tipo detectado del archivo (`csv`, `xlsx`, `parquet`).
- `table_name`: nombre de la tabla o vista registrada en DuckDB para este run.
- `schema`: lista ordenada de columnas con nombre y tipo detectado.
- `row_count`: número de filas cargadas.
- `nulls?`: resumen básico de nulos por columna, si se calcula.
- `sample?`: muestra pequeña y serializable de filas, si se expone.

### Responsabilidad
Describir el dataset disponible para análisis sin mezclar esta metadata con resultados analíticos.

### Invariantes y reglas mínimas
- Debe corresponder exactamente al dataset del run actual.
- No contiene hallazgos ni interpretación.
- Debe poder construirse después de una carga válida a DuckDB.
- `table_name` debe ser el identificador que el agente pueda usar para consultar el dataset cargado.

### Encaje en el flujo general
La capa de datos lo genera tras validar y cargar el archivo. El runtime lo incluye después dentro del contexto que recibe el agente.

---

## 3. AgentExecutionContext

### Propósito
Agrupar el contexto estructurado mínimo que necesita el agente para ejecutar el análisis.

### Campos
- `run_id`: identificador único del run actual.
- `session_id`: identificador de la sesión activa.
- `dataset_profile`: metadata del dataset disponible.
- `duckdb_context`: referencia o handle necesario para consultar el dataset cargado.
- `output_dir`: ubicación reservada para outputs del run.

### Responsabilidad
Entregar al agente todo el contexto operativo necesario sin exponerle responsabilidades de sesión, routing o parsing de interfaz.

### Invariantes y reglas mínimas
- Siempre pertenece a un único `run_id`.
- Debe contener un `DatasetProfile` válido.
- Debe apuntar a un contexto DuckDB listo para consulta.
- `output_dir` debe pertenecer al run actual.
- No debe contener lógica de render de CLI.

### Encaje en el flujo general
El runtime construye este contrato después de preparar el dataset y antes de invocar al agente.

### Nota de consistencia
El nombre congelado para este campo en el MVP es `duckdb_context`. Debe usarse de forma uniforme en la documentación y en la implementación.

---

## 4. AgentResult

### Propósito
Definir la salida estructurada del agente tras completar un análisis.

### Campos
- `narrative`: respuesta principal en lenguaje natural.
- `findings`: lista de hallazgos concretos.
- `sql_trace`: lista ordenada de consultas o intentos de consulta usados durante el análisis.
- `tables`: lista de resultados tabulares relevantes para la respuesta.
- `charts`: lista de gráficos generados o referenciados por la respuesta.
- `recommendations?`: siguientes pasos o recomendaciones accionables.
- `artifact_manifest`: índice de outputs del run.

### Responsabilidad
Separar el resultado analítico del modo en que luego la CLI lo renderiza al usuario.

### Invariantes y reglas mínimas
- Debe pertenecer a un único run.
- Debe ser interpretable sin depender del renderer CLI.
- No debe incluir routing, selección de agente ni control de sesión.
- `artifact_manifest` debe estar asociado al mismo run.
- `findings`, `sql_trace`, `tables` y `charts` pueden venir vacíos, pero deben mantener formato consistente.

### Formato esperado de `sql_trace`
`sql_trace` representa la traza analítica del run, no logs internos del motor. Cada entrada debe incluir:
- `statement`: SQL ejecutado o intentado.
- `status`: resultado mínimo de la entrada (`ok` o `error`).
- `purpose?`: motivo breve de esa consulta, si se quiere exponer.
- `rows_returned?`: número de filas devueltas, si aplica.

### Qué representan `tables` y `charts`
- `tables` representa resultados tabulares relevantes para la respuesta final o exportados como artefactos. No representa todas las tablas internas, temporales o de staging del dataset.
- `charts` representa visualizaciones generadas en el run y referenciables desde la respuesta. No representa componentes UI ni configuraciones de frontend.

### Encaje en el flujo general
El agente devuelve este contrato al runtime, y después la interfaz lo renderiza para el usuario final.

---

## 5. ArtifactManifest

### Propósito
Indexar las salidas generadas por un run para mantener trazabilidad y reproducibilidad.

### Campos
- `run_id`: run al que pertenece el manifiesto.
- `response_path?`: ubicación de la respuesta final persistida, si existe.
- `table_paths`: ubicaciones de tablas exportadas del run.
- `chart_paths`: ubicaciones de gráficos generados del run.

### Responsabilidad
Ofrecer una referencia unificada a los outputs del run sin mezclarla con la lógica de análisis.

### Invariantes y reglas mínimas
- Debe estar asociado obligatoriamente a un `run_id`.
- Solo referencia outputs del run actual.
- `table_paths` y `chart_paths` pueden ser colecciones vacías, pero no deben apuntar a outputs de otro run.

### Encaje en el flujo general
Se construye al final del run como índice de outputs y se incluye dentro de `AgentResult` para que runtime e interfaz puedan localizar las salidas generadas.

### Nota de consistencia
`ArtifactManifest` es un contrato propio del MVP. `AgentResult` lo referencia, pero no lo sustituye ni absorbe su responsabilidad.

---

## 6. Contrato mínimo de errores

### Propósito
Dar un formato común a los errores del runtime, datos, adapters y agente sin inflar el sistema.

### Campos
- `code`: identificador estable y legible por máquina.
- `message`: descripción corta y entendible del fallo.
- `stage`: etapa donde ocurrió el error.
- `details?`: contexto adicional útil para diagnóstico.

### Reglas mínimas
- `code` debe ser estable entre runs equivalentes.
- `stage` debe mapear a una etapa reconocible del flujo, por ejemplo: `request_validation`, `dataset_preparation`, `agent_resolution`, `agent_execution`, `artifact_persistence`.
- Este contrato es el esperado cuando un run termina en estado `failed`.
- No hace falta modelar jerarquías complejas de excepciones en este documento.

---

## 7. Interfaz mínima esperada del Agent Registry

### Responsabilidad mínima
- Aceptar un `agent_id`.
- Resolver ese `agent_id` a una implementación disponible.
- Exponer la configuración estática mínima necesaria para ejecutar el agente resuelto.
- Devolver un error del contrato mínimo si el agente no existe.

### Límites
- No enruta.
- No decide qué agente conviene.
- No reescribe prompts.
- No actúa como Planner encubierto.

---

## 8. Interfaz mínima esperada del adapter LLM

### Responsabilidad mínima
- Recibir un prompt ya preparado por la capa agente.
- Ejecutar la llamada al modelo fijo del MVP a través de Ollama.
- Devolver el contenido generado por el modelo.
- Traducir errores del proveedor al contrato mínimo de errores.

### Límites
- No decide el agente.
- No elige dinámicamente entre múltiples proveedores o modelos en este MVP.
- No incorpora políticas complejas de routing, retries avanzados ni fallback multi-modelo.

---

## 9. Interfaz mínima esperada del loader/profiler de dataset

### Responsabilidad mínima
- Recibir una ruta local de archivo.
- Validar existencia y formato soportado.
- Cargar el dataset en DuckDB para el run actual.
- Construir y devolver un `DatasetProfile` consistente con esa carga.
- Devolver error del contrato mínimo si la validación o la carga falla.

### Límites
- No resuelve múltiples datasets por run.
- No incorpora catálogo, sincronización remota ni conectores externos.
- No mezcla profiling técnico con hallazgos analíticos del agente.
