# OPERATIONS

## Propósito
Dar una guía operativa mínima para arrancar y diagnosticar el sistema en su estado actual, manteniendo coherencia con su dirección local-first.

## Estado operativo actual
Hoy el producto ya dispone de:
- CLI operativa (`status`, `config`, `run`);
- API local mínima para chats, runs, health e historial persistido.
- UI web local principal para chats analíticos, gráficos embebidos, readiness e historial persistido consultable.

## Requisitos mínimos
- Python con dependencias del repo.
- Node.js + npm para la UI local.
- Ollama instalado.
- Ollama levantado localmente.
- Modelo `deepseek-r1:8b` disponible.

## Arranque mínimo actual
### 1. Instalar dependencias Python
```bash
python -m pip install -r requirements.txt
```

### 2. Verificar Ollama
```bash
ollama --version
ollama list
```

### 3. Confirmar que el modelo requerido existe
Debe aparecer `deepseek-r1:8b` en la lista de modelos de Ollama.

### 4. Ejecutar una prueba manual mínima
```bash
python -m interfaces.cli --agent data_analyst --dataset DatasetV1/Walmart_Sales.csv --prompt "Resume los hallazgos principales"
```

### 5. Instalar dependencias de la UI web
```bash
npm --prefix interfaces/web install
```

### 6. Construir la UI web empaquetada
```bash
npm --prefix interfaces/web run build
```

## Chequeos operativos actuales por CLI

### Estado operativo agregado
```bash
python -m interfaces.cli status
python -m interfaces.cli status --json
```

Debe indicar:
- si la aplicación local está lista a nivel interno;
- si `ollama` está en PATH;
- si el endpoint local responde;
- si `deepseek-r1:8b` está disponible;
- qué acción tomar cuando algo falle.

### Configuración efectiva mínima
```bash
python -m interfaces.cli config
python -m interfaces.cli config --json
```

Debe exponer solo:
- `default_agent_id`;
- formatos soportados;
- endpoint del proveedor local;
- modelo requerido.

## Arranque mínimo actual de la API local

### 1. Levantar la API
```bash
python -m interfaces.api
```

Por defecto expone HTTP en `127.0.0.1:8000`.

### 2. Verificar health de aplicación
```bash
curl http://127.0.0.1:8000/health
```

Debe devolver:
- `status`;
- `ready`;
- `default_agent_id`;
- `artifacts_root`;
- `checks`.

### 3. Verificar health del proveedor
```bash
curl http://127.0.0.1:8000/health/proveedor
```

Debe devolver:
- `status`;
- `ready`;
- `proveedor`;
- `endpoint`;
- `binary_available`;
- `reachable`;
- `model`;
- `model_available`.

### 4. Crear un run por API
```bash
curl -X POST http://127.0.0.1:8000/runs ^
  -H "Content-Type: application/json" ^
  -d "{\"agent_id\":\"data_analyst\",\"dataset_path\":\"DatasetV1/Walmart_Sales.csv\",\"user_prompt\":\"Resume los hallazgos principales\"}"
```

El `POST /runs` es síncrono en esta fase y devuelve el `RunDetail` final cuando el run termina.

### 5. Consultar historial persistido
```bash
curl http://127.0.0.1:8000/chats
curl http://127.0.0.1:8000/runs
curl http://127.0.0.1:8000/runs/{run_id}
curl http://127.0.0.1:8000/runs/{run_id}/artifacts
```

La metadata persistida del run se guarda en `artifacts/runs/<run_id>/run.json`, junto a los artifacts del propio run.

### 6. Crear un chat por API
```bash
curl -X POST http://127.0.0.1:8000/chats ^
  -H "Content-Type: application/json" ^
  -d "{\"agent_id\":\"data_analyst\",\"dataset_path\":\"DatasetV1/student_lifestyle_performance_dataset.csv\",\"user_prompt\":\"dime cual es la carrera (branch) en la que mas se estudia\"}"
```

Para continuar la conversación:
```bash
curl -X POST http://127.0.0.1:8000/chats/{chat_id}/messages ^
  -H "Content-Type: application/json" ^
  -d "{\"user_prompt\":\"y comparalo con la segunda carrera\"}"
```

La metadata persistida del chat vive bajo `artifacts/chats/<chat_id>/chat.json`; los outputs técnicos siguen en `artifacts/runs/<run_id>`.

## Arranque recomendado del producto empaquetado

### 1. Construir la UI
```bash
npm --prefix interfaces/web run build
```

### 2. Levantar API + UI en un solo proceso
```bash
python -m interfaces.api --serve-web
```

Por defecto:
- la UI queda servida desde `http://127.0.0.1:8000/`;
- los assets web salen de `interfaces/web/dist`;
- la UI usa la API local por mismo origen;
- los endpoints API siguen disponibles en el mismo proceso.

### 3. Recorrido mínimo esperado en packaging local
- abrir `http://127.0.0.1:8000/`;
- comprobar readiness de aplicación y proveedor;
- revisar que los chats persistidos cargan;
- introducir `DatasetV1/student_lifestyle_performance_dataset.csv` como ruta manual;
- crear un chat con una pregunta inicial;
- revisar narrativa, hallazgos, gráficos embebidos y exportaciones técnicas colapsadas;
- enviar una pregunta de seguimiento sobre el mismo dataset.

### 4. Fallo esperado si falta la build
Si `interfaces/web/dist/index.html` no existe, `python -m interfaces.api --serve-web` falla con error claro y pide ejecutar:

```bash
npm --prefix interfaces/web run build
```

## Arranque mínimo actual de la UI web local

### 1. Confirmar que la API local está levantada
La UI usa `/api` con proxy local hacia `http://127.0.0.1:8000`, así que la API debe estar arrancada antes.

### 2. Levantar la UI
```bash
npm --prefix interfaces/web run dev
```

Por defecto la UI queda disponible en `http://127.0.0.1:4173`.

### 3. Recorrido mínimo esperado
- abrir `http://127.0.0.1:4173`;
- comprobar el readiness de aplicación y proveedor;
- revisar que los chats persistidos cargan y que selecciona el chat más reciente;
- introducir `DatasetV1/student_lifestyle_performance_dataset.csv` como ruta manual;
- crear un chat con un prompt simple;
- revisar narrativa, hallazgos, tablas y gráficos del chat seleccionado;
- cambiar a un chat previo y verificar su detalle persistido aunque el proveedor no esté listo para nuevos submits.

## Health y readiness esperados
El producto distingue entre:

### Health de aplicación
En la Fase 1 indica si la aplicación local tiene wiring/configuración válidos para operar:
- agente por defecto resoluble;
- directorio de artifacts utilizable;
- configuración mínima disponible.

### Health del proveedor
Indica si:
- `ollama` está disponible en PATH;
- Ollama responde;
- el endpoint local es accesible;
- el modelo `deepseek-r1:8b` está disponible.

La API local expone ambos chequeos de forma explícita.

## Entrada actual documentada del dataset
La fase producto actual sigue usando **ruta manual local** como entrada del dataset. Eso mantiene coherencia con el flujo actual del repositorio y con el contrato `dataset_path`.

## Historial persistente local actual
La operación local ya puede consultar historial persistente de chats y runs por API y por la UI web:
- `GET /chats`;
- `GET /chats/{chat_id}`;
- `GET /runs`;
- `GET /runs/{run_id}`;
- `GET /runs/{run_id}/artifacts`.

La fuente de verdad para ese historial es la metadata file-backed que vive junto a cada run en el espacio de artifacts.
La UI consume esos mismos contratos para listar chats previos, seleccionar una conversación y revisar resultados visuales sin depender solo del proceso actual.

## Packaging local actual
La forma recomendada de distribución local en esta fase es repo-local y monoproceso:
- instalar dependencias Python y web;
- construir `interfaces/web/dist`;
- arrancar `python -m interfaces.api --serve-web`.

No se introducen todavía zip, binario, instalador ni bundle autónomo fuera del repo.

## Runner operativo de Fase 7
La validación repo-local queda formalizada en tres lanes:

```bash
python scripts/ci_checks.py python
python scripts/ci_checks.py web
python scripts/ci_checks.py smoke
```

Semántica operativa:
- `python` valida core, API y E2E Python rápidos;
- `web` valida build empaquetada y browser E2E;
- `smoke` valida estado operativo real, integraciones reales con Ollama y la CLI sobre host preparado.

La validación manual final del runtime empaquetado se mantiene aparte:

```bash
python -m interfaces.api --serve-web
```

## Troubleshooting básico

### `npm --prefix interfaces/web run build` falla con `spawn EPERM`
Síntoma:
- el build web falla en este entorno Windows sandbox con `Error: spawn EPERM`.

Lectura:
- restricción del sandbox/tooling, no regresión del producto.

Acción:
- correr el lane `python scripts/ci_checks.py web` en host real o en CI.

### `ollama` no está en PATH
Síntoma:
- `ollama --version` falla;
- `python -m interfaces.cli status` marca `binary_available: no`.

Lectura:
- problema de instalación local, no del core del producto.

### Ollama está instalado pero no responde
Síntoma:
- el binario existe pero la generación o readiness falla;
- `python -m interfaces.cli status` marca `reachable: no`.

Lectura:
- el servicio no está levantado o no está accesible en `127.0.0.1:11434`.

### El modelo requerido no aparece
Síntoma:
- `ollama list` no muestra `deepseek-r1:8b`;
- `python -m interfaces.cli status` marca `model_available: no`.

Lectura:
- falta preparar el modelo local requerido por el producto.

### Dataset inexistente o formato no soportado
Síntoma:
- el run falla en validación o preparación del dataset.

Lectura:
- el problema pertenece a entrada local, no al agente.

### El run falla pero no hay artifacts esperados
Síntoma:
- no se encuentra `response.md` o tablas exportadas del run.

Lectura:
- el fallo ocurrió antes de persistencia de artifacts o durante ella.

## Qué deberá cubrir esta guía más adelante
Cuando crezca la observabilidad, esta guía deberá ampliarse con:
- cómo leer logs estructurados;
- cómo ejecutar smoke UI + API + proveedor;
- cómo diagnosticar correlación por `session_id` y `run_id`.

## Logs estructurados mínimos actuales
La Fase 5 añade logs JSON a consola para API, CLI y runtime.

### Qué campos mínimos esperar
- `event`;
- `trace_id`;
- `session_id` cuando exista;
- `run_id` cuando exista;
- `level`;
- `logger`;
- `duration_ms` en eventos de cierre cuando aplique.

### Eventos operativos principales
- `command_started` para CLI;
- `request_started` y `request_completed` para CLI/API;
- `run_started`, `dataset_preparing`, `agent_running`, `run_succeeded`, `run_failed` para runtime.

### Cómo correlacionar un error desde API/UI
1. Capturar `trace_id` desde el cuerpo del error o del header `X-Trace-Id`.
2. Buscar en los logs JSON ese mismo `trace_id`.
3. Si el request llegó a crear run, seguir además `run_id` y `session_id`.
4. Usar `details.category` para distinguir si el fallo pertenece a `request`, `dataset`, `provider` o `core`.
