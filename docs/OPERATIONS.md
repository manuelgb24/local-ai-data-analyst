# OPERATIONS

## Propósito
Dar una guía operativa mínima para arrancar y diagnosticar el sistema en su estado actual, manteniendo coherencia con su dirección local-first.

## Estado operativo actual
Hoy el producto ya dispone de:
- CLI operativa (`status`, `config`, `run`);
- API local mínima para runs, health e historial persistido.
- UI web local principal para readiness, lanzamiento de runs e historial persistido consultable.

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
curl http://127.0.0.1:8000/runs
curl http://127.0.0.1:8000/runs/{run_id}
curl http://127.0.0.1:8000/runs/{run_id}/artifacts
```

La metadata persistida del run se guarda en `artifacts/runs/<run_id>/run.json`, junto a los artifacts del propio run.

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
- revisar que el historial persistido carga y que selecciona el run más reciente;
- introducir `DatasetV1/Walmart_Sales.csv` como ruta manual;
- lanzar el run con un prompt simple;
- revisar narrativa, hallazgos, tablas y artifacts del run seleccionado;
- cambiar a un run previo del historial y verificar su detalle persistido aunque el proveedor no esté listo para nuevos submits.

## Health y readiness esperados
Aunque la superficie HTTP todavía no esté implementada, el producto debe distinguir entre:

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

La futura API local deberá exponer ambos chequeos de forma explícita.

## Entrada futura documentada del dataset
La etapa futura aprobada sigue usando **ruta manual local** como entrada del dataset. Eso mantiene coherencia con el flujo actual del repositorio y con el contrato `dataset_path`.

## Historial persistente local actual
La operación local ya puede consultar historial persistente de runs por API y por la UI web:
- `GET /runs`;
- `GET /runs/{run_id}`;
- `GET /runs/{run_id}/artifacts`.

La fuente de verdad para ese historial es la metadata file-backed que vive junto a cada run en el espacio de artifacts.
La UI consume esos mismos contratos para listar runs previos, seleccionar un run y revisar su detalle/artifacts sin depender solo del proceso actual.

## Troubleshooting básico

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
