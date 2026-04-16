# RELEASE_CHECKLIST

## Propósito
Definir la checklist mínima para publicar una versión usable del producto sin depender de pasos implícitos.

## 1. Alcance y documentación
- [ ] La versión respeta `docs/PRODUCT_SCOPE.md`.
- [ ] `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/CONTRACTS.md` y `docs/DECISIONS.md` están al día.
- [ ] `README.md`, `docs/OPERATIONS.md` y `docs/TASKS.md` reflejan el comportamiento real y la secuencia vigente.
- [ ] `docs/TASKS.md`, `docs/CONTRACTS.md`, `docs/PRODUCT_SCOPE.md` y `docs/ARCHITECTURE.md` son coherentes entre sí.

## 2. Validación del core
- [ ] `pytest tests/unit -q`
- [ ] `pytest tests/integration -q`
- [ ] `pytest tests/e2e -q`

## 3. Validación real local
- [ ] `pytest tests/smoke/test_ollama_adapter.py -q -rs`
- [ ] `pytest tests/smoke/test_real_cli_workflow.py -q -rs`
- [ ] Ollama responde en local.
- [ ] `deepseek-r1:8b` está disponible.

## 4. Validación de la siguiente fase del producto
Aplicar cuando exista cada superficie:

### API local
- [ ] Contract tests de `POST /runs` con `dataset_path` manual.
- [ ] Contract tests de `GET /runs`.
- [ ] Contract tests de `GET /runs/{run_id}`.
- [ ] Contract tests de `GET /runs/{run_id}/artifacts`.
- [ ] Health de aplicación verificado.
- [ ] Health del proveedor verificado en `GET /health/proveedor`.
- [ ] `python -m interfaces.api --serve-web` arranca sin errores cuando la build existe.

### UI web
- [ ] `npm --prefix interfaces/web run build`
- [ ] `npm --prefix interfaces/web run test:e2e`
- [ ] Browser E2E del flujo principal con ruta manual de dataset.
- [ ] Revisión manual de errores operativos visibles.
- [ ] Acceso correcto a resultados y artifacts del último run.
- [ ] La UI empaquetada carga desde `http://127.0.0.1:8000/` y consume la API por mismo origen.

## 5. Operación y soporte
- [ ] Los errores importantes son trazables.
- [ ] La documentación de troubleshooting cubre los fallos más comunes.
- [ ] Los pasos de arranque local son reproducibles.
- [ ] El historial persistente local es coherente con los artifacts disponibles.
- [ ] `docs/INSTALLATION.md` refleja la historia real de build + arranque monoproceso.

## 6. Decisiones de no-scope confirmadas
- [ ] No se introdujo Planner.
- [ ] No se introdujo routing automático.
- [ ] No se introdujo multi-agent real.
- [ ] No se introdujo backend hosted.
- [ ] No se introdujo auth o multiusuario accidentalmente.

## 7. Checklist manual final
- [ ] Un run válido produce narrativa y artifacts trazables.
- [ ] Un error operativo real produce feedback entendible.
- [ ] La versión puede explicarse y operarse sin conocimiento informal extra.
