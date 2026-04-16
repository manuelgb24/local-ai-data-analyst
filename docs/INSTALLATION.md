# INSTALLATION

## Propósito
Dejar una historia reproducible de instalación, build y arranque local del producto sin depender de memoria informal.

## Requisitos
- Python con soporte para instalar `requirements.txt`.
- Node.js + npm para construir la UI web.
- Ollama instalado y levantado localmente.
- Modelo `deepseek-r1:8b` disponible en Ollama.

## Instalación mínima

### 1. Instalar dependencias Python
```bash
python -m pip install -r requirements.txt
```

### 2. Instalar dependencias web
```bash
npm --prefix interfaces/web install
```

### 3. Verificar el proveedor local
```bash
ollama --version
ollama list
python -m interfaces.cli status --json
```

Debe aparecer `deepseek-r1:8b` como modelo disponible y `ready: true` en la salida de `status --json`.

## Arranque recomendado del producto

### 1. Construir la UI empaquetada
```bash
npm --prefix interfaces/web run build
```

### 2. Levantar API + UI en un solo proceso
```bash
python -m interfaces.api --serve-web
```

Por defecto:
- la aplicación queda disponible en `http://127.0.0.1:8000/`;
- la UI build se sirve desde el mismo proceso;
- la UI usa la API local por mismo origen;
- los endpoints API siguen disponibles en `/health`, `/health/proveedor`, `/runs`, `/runs/{run_id}` y `/runs/{run_id}/artifacts`.

## Validación mínima tras instalar
1. Abrir `http://127.0.0.1:8000/`.
2. Confirmar que la UI carga.
3. Verificar readiness de aplicación y proveedor.
4. Comprobar que el historial persistido carga.
5. Lanzar un run con `DatasetV1/Walmart_Sales.csv`.
6. Revisar narrativa, hallazgos y artifacts.

## Modo de desarrollo que se mantiene
El flujo recomendado para packaging usa un solo proceso en runtime, pero el flujo de desarrollo sigue siendo:

```bash
python -m interfaces.api
npm --prefix interfaces/web run dev
```

En ese modo la UI usa `/api` con proxy local hacia `http://127.0.0.1:8000`.

## Fallo esperado si falta la build web
Si se ejecuta:

```bash
python -m interfaces.api --serve-web
```

sin haber generado antes `interfaces/web/dist`, la API falla con error claro y pide ejecutar:

```bash
npm --prefix interfaces/web run build
```
