# INSTALLATION

## Proposito
Dejar una historia reproducible de instalacion, build y arranque local del producto sin depender de memoria informal.

## Requisitos
- Python con soporte para instalar `requirements.txt`.
- `requirements-dev.txt` para ejecutar validaciones repo-locales y CI local.
- Node.js + npm para construir la UI web.
- Ollama instalado y levantado localmente.
- Modelo `deepseek-r1:8b` disponible en Ollama.

## Instalacion minima

### 1. Instalar dependencias Python
```bash
python -m pip install -r requirements.txt
```

Para validación y release hardening:

```bash
python -m pip install -r requirements-dev.txt
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
- la aplicacion queda disponible en `http://127.0.0.1:8000/`;
- la UI build se sirve desde el mismo proceso;
- la UI usa la API local por mismo origen;
- los endpoints API siguen disponibles en `/health`, `/health/proveedor`, `/runs`, `/runs/{run_id}` y `/runs/{run_id}/artifacts`.

## Validacion minima tras instalar
1. Abrir `http://127.0.0.1:8000/`.
2. Confirmar que la UI carga.
3. Verificar readiness de aplicacion y proveedor.
4. Comprobar que el historial persistido carga.
5. Lanzar un run con `DatasetV1/Walmart_Sales.csv`.
6. Revisar narrativa, hallazgos y artifacts.

## Validacion repo-local de Fase 7
Una vez instalado el producto, la validacion operativa queda agrupada en:

```bash
python scripts/ci_checks.py python
python scripts/ci_checks.py web
python scripts/ci_checks.py smoke
```

Reglas:
- `python` y `web` son los gates automatizables;
- `smoke` exige Ollama real y `deepseek-r1:8b` disponibles antes de ejecutarse;
- el smoke manual final de packaging sigue siendo `python -m interfaces.api --serve-web`.

Nota operativa:
- si `npm --prefix interfaces/web run build` falla con `spawn EPERM` en este sandbox Windows, valida el lane `web` fuera del sandbox o en CI; no es un bug del producto.

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
