# 3_agents

`3_agents` es un producto **local-first** para analizar datasets externos desde archivos locales mediante un agente especializado.

## Estado del proyecto
El repositorio ya tiene cerrado el **MVP funcional**:
- CLI end-to-end;
- un agente real (`data_analyst`);
- carga de `csv`, `xlsx` y `parquet`;
- análisis sobre DuckDB local;
- modelo fijo `deepseek-r1:8b` vía Ollama;
- artifacts trazables por run;
- tests unitarios, de integración, E2E y smoke mínimos.

La fase actual del proyecto ya no es “construir el MVP”, sino **evolucionarlo a producto**.

## Dirección actual del producto
La siguiente etapa aprobada es:
- **Web + API** como interfaz principal;
- **local-first** como modelo operativo;
- **monorepo único**;
- **CLI** mantenida como interfaz operativa y técnica.

El núcleo funcional sigue congelado por ahora:
- un solo agente real;
- un dataset por run;
- entrada por ruta manual local;
- DuckDB local;
- Ollama local;
- sin Planner, sin routing automático y sin multi-agent real.

## Estructura del repo hoy
- `interfaces/cli` — interfaz operativa actual.
- `application` — casos de uso.
- `runtime` — coordinación del run.
- `agents/data_analyst` — agente analítico actual.
- `data` — preparación de datasets.
- `artifacts` — outputs y manifest.
- `adapters` — integraciones con DuckDB y Ollama.
- `tests` — unit, integration, e2e y smoke.
- `docs` — arquitectura, contratos, decisiones, alcance, operación y checklist de release.

## Cómo arrancar el MVP actual
### Requisitos
- Python con dependencias de `requirements.txt`
- Ollama levantado localmente
- modelo `deepseek-r1:8b` disponible en Ollama

### Instalar dependencias Python
```bash
python -m pip install -r requirements.txt
```

### Verificar Ollama
```bash
ollama --version
ollama list
```

### Ejecutar la CLI
```bash
python -m interfaces.cli --agent data_analyst --dataset DatasetV1/Walmart_Sales.csv --prompt "Resume los hallazgos principales"
```

### Ver estado operativo y configuración
```bash
python -m interfaces.cli status
python -m interfaces.cli config
```

## Documentación clave
- `docs/TASKS.md` — guía principal futura y roadmap operativo canónico.
- `AGENTS.md` — guardrails del repo y reglas de trabajo.
- `docs/PROJECT_BRIEF.md` — objetivo y dirección del producto.
- `docs/ARCHITECTURE.md` — arquitectura actual y evolución prevista.
- `docs/CONTRACTS.md` — contratos del core y de la futura API local.
- `docs/DECISIONS.md` — decisiones de producto y arquitectura.
- `docs/TEST_PLAN.md` — estrategia de validación.
- `docs/OPERATIONS.md` — operación local y troubleshooting.
- `docs/RELEASE_CHECKLIST.md` — checklist de release.
- `docs/PRODUCT_SCOPE.md` — límites actuales del producto.

## Hacia dónde va ahora
La siguiente secuencia de trabajo vive en `docs/TASKS.md` y arranca, tras el cierre del MVP, con:
- Fase 1 — readiness, configuración y UX operativa local;
- Fase 2 — API local mínima;
- Fase 3 — interfaz principal con ruta manual de dataset;
- Fase 4 — historial persistente de runs y artifacts;
- Fase 5 — observabilidad del producto;
- Fase 6 — packaging y distribución local;
- Fase 7 — CI y release hardening.
