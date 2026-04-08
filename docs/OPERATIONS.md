# OPERATIONS

## Propósito
Dar una guía operativa mínima para arrancar y diagnosticar el sistema en su estado actual, manteniendo coherencia con su dirección local-first.

## Estado operativo actual
Hoy la superficie operativa real es la CLI. La siguiente fase añadirá UI web y API local, pero esta guía ya fija los chequeos que deberán seguir siendo válidos.

## Requisitos mínimos
- Python con dependencias del repo.
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

## Historial persistente local previsto
La operación futura del producto deberá poder consultar historial persistente local de runs, no solo el run actual del proceso en memoria. Esa capacidad debe mantenerse alineada con la persistencia local de metadata y con el espacio de artifacts.

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
Cuando existan API local y UI web, esta guía deberá ampliarse con:
- cómo arrancar la aplicación local completa;
- cómo verificar `/health` y `/health/proveedor`;
- cómo leer logs estructurados;
- cómo consultar historial persistente local de runs;
- cómo ejecutar smoke UI + API + proveedor.
