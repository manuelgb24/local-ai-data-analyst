"""FastAPI app for the local-first Phase 2 API surface."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
from uuid import uuid4

import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

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
from observability import OperationalReadinessService, build_default_operational_readiness_service
from runtime import InMemoryRunTracker, RuntimeCoordinator, build_default_agent_registry

from .models import CreateRunRequestPayload
from .serializers import build_api_error, serialize_response

DEFAULT_API_HOST = "127.0.0.1"
DEFAULT_API_PORT = 8000
DEFAULT_ARTIFACTS_ROOT = "artifacts/runs"
_PROVIDER_UNAVAILABLE_CODES = frozenset({"llm_provider_unavailable"})


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
) -> FastAPI:
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

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(request, exc: RequestValidationError) -> JSONResponse:  # type: ignore[no-untyped-def]
        trace_id = _trace_id()
        return JSONResponse(
            status_code=400,
            content=build_api_error(
                code="invalid_request",
                message="Request payload failed validation",
                status=400,
                details={"errors": exc.errors()},
                trace_id=trace_id,
            ),
        )

    @app.exception_handler(RunError)
    async def handle_run_error(request, exc: RunError) -> JSONResponse:  # type: ignore[no-untyped-def]
        status_code = _status_code_for_run_error(exc)
        trace_id = _trace_id()
        details = {"stage": exc.stage.value}
        if exc.details:
            details["context"] = exc.details
        return JSONResponse(
            status_code=status_code,
            content=build_api_error(
                code=exc.code,
                message=exc.message,
                status=status_code,
                details=details,
                trace_id=trace_id,
            ),
        )

    @app.exception_handler(RunNotFoundError)
    async def handle_run_not_found(request, exc: RunNotFoundError) -> JSONResponse:  # type: ignore[no-untyped-def]
        trace_id = _trace_id()
        return JSONResponse(
            status_code=404,
            content=build_api_error(
                code="run_not_found",
                message=f"Run not found: {exc.run_id}",
                status=404,
                details={"run_id": exc.run_id},
                trace_id=trace_id,
            ),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request, exc: Exception) -> JSONResponse:  # type: ignore[no-untyped-def]
        trace_id = _trace_id()
        return JSONResponse(
            status_code=500,
            content=build_api_error(
                code="unexpected_api_error",
                message="Unexpected API error",
                status=500,
                details={"error_type": type(exc).__name__},
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

    return app


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m interfaces.api",
        description="Run the local-first Phase 2 API server.",
    )
    parser.add_argument("--host", default=DEFAULT_API_HOST, help="Host interface to bind.")
    parser.add_argument("--port", type=int, default=DEFAULT_API_PORT, help="TCP port for the local API.")
    parser.add_argument(
        "--artifacts-root",
        default=DEFAULT_ARTIFACTS_ROOT,
        help="Filesystem root used for run artifacts and persisted metadata.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    uvicorn.run(
        create_app(artifacts_root=args.artifacts_root),
        host=args.host,
        port=args.port,
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


def _trace_id() -> str:
    return uuid4().hex

