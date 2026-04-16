"""FastAPI app for the local-first Phase 2 API surface."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
from time import perf_counter

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from application import (
    ErrorStage,
    GetRunUseCase,
    ListRunArtifactsUseCase,
    ListRunsUseCase,
    RunAnalysisUseCase,
    RunError,
    RunNotFoundError,
    RunRequest,
)
from artifacts import FilesystemRunMetadataStore
from data import LocalDatasetPreparer
from observability import (
    ERROR_CATEGORY_CORE,
    ERROR_CATEGORY_REQUEST,
    OperationalReadinessService,
    bound_context,
    build_api_error_details,
    build_default_operational_readiness_service,
    classify_run_error,
    configure_structured_logging,
    generate_trace_id,
    get_logger,
    log_event,
)
from runtime import InMemoryRunTracker, RuntimeCoordinator, build_default_agent_registry

from .models import CreateRunRequestPayload
from .serializers import build_api_error, serialize_response

DEFAULT_API_HOST = "127.0.0.1"
DEFAULT_API_PORT = 8000
DEFAULT_ARTIFACTS_ROOT = "artifacts/runs"
DEFAULT_WEB_DIST = Path(__file__).resolve().parents[1] / "web" / "dist"
_PROVIDER_UNAVAILABLE_CODES = frozenset({"llm_provider_unavailable"})
_LOGGER = get_logger("api")


def build_default_run_metadata_store(
    artifacts_root: str | Path = DEFAULT_ARTIFACTS_ROOT,
) -> FilesystemRunMetadataStore:
    return FilesystemRunMetadataStore(artifacts_root=artifacts_root)


def build_default_runtime_coordinator(
    *,
    artifacts_root: str | Path = DEFAULT_ARTIFACTS_ROOT,
    run_metadata_store: FilesystemRunMetadataStore | None = None,
) -> RuntimeCoordinator:
    store = run_metadata_store or build_default_run_metadata_store(artifacts_root=artifacts_root)
    return RuntimeCoordinator(
        dataset_preparer=LocalDatasetPreparer(),
        agent_registry=build_default_agent_registry(),
        tracker=InMemoryRunTracker(on_change=store.save),
        artifacts_root=artifacts_root,
    )


def create_app(
    *,
    artifacts_root: str | Path = DEFAULT_ARTIFACTS_ROOT,
    runtime_coordinator: RuntimeCoordinator | None = None,
    operational_readiness_service: OperationalReadinessService | None = None,
    run_metadata_store: FilesystemRunMetadataStore | None = None,
    serve_web: bool = False,
    web_dist: str | Path | None = None,
) -> FastAPI:
    configure_structured_logging()
    store = run_metadata_store or build_default_run_metadata_store(artifacts_root=artifacts_root)
    coordinator = runtime_coordinator or build_default_runtime_coordinator(
        artifacts_root=artifacts_root,
        run_metadata_store=store,
    )
    readiness_service = operational_readiness_service or build_default_operational_readiness_service(
        artifacts_root=artifacts_root,
    )

    run_use_case = RunAnalysisUseCase(runtime=coordinator)
    list_runs_use_case = ListRunsUseCase(store)
    get_run_use_case = GetRunUseCase(store)
    list_artifacts_use_case = ListRunArtifactsUseCase(store)

    app = FastAPI(
        title="3_agents local API",
        summary="Local-first API surface over the existing data_analyst core.",
        version="0.2.0",
    )

    @app.middleware("http")
    async def add_trace_id_and_request_logs(request: Request, call_next):  # type: ignore[no-untyped-def]
        trace_id = generate_trace_id()
        request.state.trace_id = trace_id
        started_at = perf_counter()

        with bound_context(
            trace_id=trace_id,
            interface="api",
            method=request.method,
            path=request.url.path,
        ):
            log_event(_LOGGER, "request_started")
            response = await call_next(request)
            response.headers["X-Trace-Id"] = trace_id
            log_event(
                _LOGGER,
                "request_completed",
                status_code=response.status_code,
                duration_ms=round((perf_counter() - started_at) * 1000, 2),
            )
            return response

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        trace_id = _trace_id(request)
        log_event(
            _LOGGER,
            "request_failed",
            level=40,
            code="invalid_request",
            category=ERROR_CATEGORY_REQUEST,
            status_code=400,
        )
        return JSONResponse(
            status_code=400,
            headers={"X-Trace-Id": trace_id},
            content=build_api_error(
                code="invalid_request",
                message="Request payload failed validation",
                status=400,
                details=build_api_error_details(
                    category=ERROR_CATEGORY_REQUEST,
                    stage=ErrorStage.REQUEST_VALIDATION.value,
                    errors=exc.errors(),
                ),
                trace_id=trace_id,
            ),
        )

    @app.exception_handler(RunError)
    async def handle_run_error(request: Request, exc: RunError) -> JSONResponse:
        status_code = _status_code_for_run_error(exc)
        trace_id = _trace_id(request)
        category = classify_run_error(exc)
        error_context = None if not exc.details else {key: value for key, value in exc.details.items() if key != "category"}
        details = build_api_error_details(
            category=category,
            stage=exc.stage.value,
            context=error_context,
        )
        log_event(
            _LOGGER,
            "request_failed",
            level=40,
            code=exc.code,
            category=category,
            stage=exc.stage.value,
            status_code=status_code,
        )
        return JSONResponse(
            status_code=status_code,
            headers={"X-Trace-Id": trace_id},
            content=build_api_error(
                code=exc.code,
                message=exc.message,
                status=status_code,
                details=details,
                trace_id=trace_id,
            ),
        )

    @app.exception_handler(RunNotFoundError)
    async def handle_run_not_found(request: Request, exc: RunNotFoundError) -> JSONResponse:
        trace_id = _trace_id(request)
        log_event(
            _LOGGER,
            "request_failed",
            level=40,
            code="run_not_found",
            category=ERROR_CATEGORY_REQUEST,
            status_code=404,
        )
        return JSONResponse(
            status_code=404,
            headers={"X-Trace-Id": trace_id},
            content=build_api_error(
                code="run_not_found",
                message=f"Run not found: {exc.run_id}",
                status=404,
                details=build_api_error_details(
                    category=ERROR_CATEGORY_REQUEST,
                    run_id=exc.run_id,
                ),
                trace_id=trace_id,
            ),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        trace_id = _trace_id(request)
        log_event(
            _LOGGER,
            "request_failed",
            level=40,
            code="unexpected_api_error",
            category=ERROR_CATEGORY_CORE,
            status_code=500,
            error_type=type(exc).__name__,
        )
        return JSONResponse(
            status_code=500,
            headers={"X-Trace-Id": trace_id},
            content=build_api_error(
                code="unexpected_api_error",
                message="Unexpected API error",
                status=500,
                details=build_api_error_details(
                    category=ERROR_CATEGORY_CORE,
                    error_type=type(exc).__name__,
                ),
                trace_id=trace_id,
            ),
        )

    @app.post("/runs")
    def create_run(payload: CreateRunRequestPayload) -> JSONResponse:
        request = _build_run_request(payload)
        result = run_use_case.execute(request)
        detail = get_run_use_case.execute(result.artifact_manifest.run_id)
        return JSONResponse(status_code=200, content=serialize_response(detail))

    @app.get("/runs")
    def list_runs() -> JSONResponse:
        return JSONResponse(status_code=200, content=serialize_response(list_runs_use_case.execute()))

    @app.get("/runs/{run_id}")
    def get_run(run_id: str) -> JSONResponse:
        return JSONResponse(status_code=200, content=serialize_response(get_run_use_case.execute(run_id)))

    @app.get("/runs/{run_id}/artifacts")
    def get_run_artifacts(run_id: str) -> JSONResponse:
        return JSONResponse(status_code=200, content=serialize_response(list_artifacts_use_case.execute(run_id)))

    @app.get("/health")
    def get_health() -> JSONResponse:
        return JSONResponse(status_code=200, content=serialize_response(readiness_service.get_application_health()))

    @app.get("/health/proveedor")
    def get_provider_health() -> JSONResponse:
        return JSONResponse(status_code=200, content=serialize_response(readiness_service.get_provider_health()))

    if serve_web:
        app.mount(
            "/",
            StaticFiles(directory=str(validate_web_dist(web_dist)), html=True),
            name="web",
        )

    return app


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m interfaces.api",
        description="Run the local-first API server, optionally serving the packaged web UI.",
    )
    parser.add_argument("--host", default=DEFAULT_API_HOST, help="Host interface to bind.")
    parser.add_argument("--port", type=int, default=DEFAULT_API_PORT, help="TCP port for the local API.")
    parser.add_argument(
        "--artifacts-root",
        default=DEFAULT_ARTIFACTS_ROOT,
        help="Filesystem root used for run artifacts and persisted metadata.",
    )
    parser.add_argument(
        "--serve-web",
        action="store_true",
        help="Serve the built web UI from the same local API process.",
    )
    parser.add_argument(
        "--web-dist",
        default=None,
        help="Optional filesystem path to the built web UI directory. Defaults to interfaces/web/dist.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        app = create_app(
            artifacts_root=args.artifacts_root,
            serve_web=args.serve_web,
            web_dist=args.web_dist,
        )
    except ValueError as exc:
        parser.exit(status=2, message=f"error: {exc}\n")

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        access_log=False,
        log_config=None,
    )
    return 0


def _build_run_request(payload: CreateRunRequestPayload) -> RunRequest:
    try:
        return RunRequest(
            agent_id=payload.agent_id,
            dataset_path=payload.dataset_path,
            user_prompt=payload.user_prompt,
            session_id=payload.session_id,
        )
    except (TypeError, ValueError) as exc:
        raise RunError(
            code="invalid_request",
            message=str(exc),
            stage=ErrorStage.REQUEST_VALIDATION,
        ) from exc


def _status_code_for_run_error(error: RunError) -> int:
    if error.code in _PROVIDER_UNAVAILABLE_CODES:
        return 503
    if error.stage in {ErrorStage.REQUEST_VALIDATION, ErrorStage.DATASET_PREPARATION, ErrorStage.AGENT_RESOLUTION}:
        return 400
    if error.stage is ErrorStage.ARTIFACT_PERSISTENCE:
        return 500
    if error.stage is ErrorStage.AGENT_EXECUTION:
        return 500
    return 500


def resolve_web_dist(web_dist: str | Path | None = None) -> Path:
    candidate = DEFAULT_WEB_DIST if web_dist is None else Path(web_dist).expanduser()
    return candidate.resolve()


def validate_web_dist(web_dist: str | Path | None = None) -> Path:
    resolved = resolve_web_dist(web_dist)
    index_path = resolved / "index.html"
    if not resolved.is_dir() or not index_path.is_file():
        raise ValueError(
            "UI build not found at "
            f"'{resolved}'. Run 'npm --prefix interfaces/web run build' before using --serve-web."
        )
    return resolved


def _trace_id(request: Request | None = None) -> str:
    if request is not None:
        trace_id = getattr(request.state, "trace_id", None)
        if isinstance(trace_id, str) and trace_id.strip():
            return trace_id
    return generate_trace_id()
