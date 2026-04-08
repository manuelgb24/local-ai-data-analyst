"""Runtime coordinator for the MVP run flow."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from application.contracts import AgentExecutionContext, AgentResult, ErrorStage, RunError, RunRequest, RunState
from artifacts import FilesystemArtifactPersister
from data import PreparedDataset

from .registry import AgentRegistry
from .tracker import InMemoryRunTracker

DatasetPreparer = Callable[[RunRequest, str], PreparedDataset]
ArtifactPersister = Callable[[AgentResult, str | Path], object]


class RuntimeCoordinator:
    """Coordinates the minimal run flow without knowing concrete infrastructure."""

    def __init__(
        self,
        dataset_preparer: DatasetPreparer,
        agent_registry: AgentRegistry,
        tracker: InMemoryRunTracker | None = None,
        artifact_persister: ArtifactPersister | None = None,
        artifacts_root: str | Path = "artifacts/runs",
    ) -> None:
        self._dataset_preparer = dataset_preparer
        self._agent_registry = agent_registry
        self._tracker = tracker or InMemoryRunTracker()
        self._artifact_persister = artifact_persister or FilesystemArtifactPersister()
        self._artifacts_root = Path(artifacts_root)

    @property
    def tracker(self) -> InMemoryRunTracker:
        return self._tracker

    def run(self, request: RunRequest) -> AgentResult:
        if not isinstance(request, RunRequest):
            raise TypeError("request must be a RunRequest instance")

        record = self._tracker.start_run(request)
        current_stage = ErrorStage.AGENT_RESOLUTION
        prepared_dataset: PreparedDataset | None = None
        result: AgentResult | None = None
        pending_error: RunError | None = None

        try:
            registered_agent = self._agent_registry.resolve(request.agent_id)

            self._tracker.mark_preparing_dataset(record.run_id)
            current_stage = ErrorStage.DATASET_PREPARATION

            output_dir = self._reserve_output_dir(record.run_id)
            prepared_dataset = self._dataset_preparer(request, record.run_id)

            context = AgentExecutionContext(
                run_id=record.run_id,
                session_id=record.session_id,
                dataset_profile=prepared_dataset.dataset_profile,
                duckdb_context=prepared_dataset.duckdb_context,
                output_dir=str(output_dir),
            )

            self._tracker.mark_running_agent(record.run_id)
            current_stage = ErrorStage.AGENT_EXECUTION

            result = registered_agent.executor(request, context)
            result.artifact_manifest = self._persist_artifacts(result, output_dir)
        except RunError as error:
            pending_error = error
        except Exception as exc:
            pending_error = self._wrap_unexpected_error(record.run_id, current_stage, exc)

        cleanup_error = self._cleanup_prepared_dataset(prepared_dataset)
        if pending_error is not None:
            self._tracker.mark_failed(record.run_id, pending_error)
            raise pending_error

        if cleanup_error is not None:
            wrapped_cleanup_error = self._wrap_unexpected_error(record.run_id, current_stage, cleanup_error)
            self._tracker.mark_failed(record.run_id, wrapped_cleanup_error)
            raise wrapped_cleanup_error from cleanup_error

        if result is None:
            unreachable_error = self._wrap_unexpected_error(
                record.run_id,
                current_stage,
                RuntimeError("Runtime finished without result or error"),
            )
            self._tracker.mark_failed(record.run_id, unreachable_error)
            raise unreachable_error

        self._tracker.mark_succeeded(record.run_id, result)
        return result

    def _reserve_output_dir(self, run_id: str) -> Path:
        self._artifacts_root.mkdir(parents=True, exist_ok=True)
        output_dir = self._artifacts_root / run_id
        output_dir.mkdir(parents=True, exist_ok=False)
        return output_dir

    def _persist_artifacts(self, result: AgentResult, output_dir: Path) -> object:
        try:
            return self._artifact_persister(result, output_dir)
        except RunError:
            raise
        except Exception as exc:
            raise RunError(
                code="artifact_persistence_failed",
                message="Artifacts could not be persisted",
                stage=ErrorStage.ARTIFACT_PERSISTENCE,
                details={
                    "run_id": result.artifact_manifest.run_id,
                    "output_dir": str(output_dir.resolve()),
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                },
            ) from exc

    def _wrap_unexpected_error(self, run_id: str, stage: ErrorStage, exc: Exception) -> RunError:
        record = self._tracker.get(run_id)
        if record.state is RunState.RUNNING_AGENT:
            stage = ErrorStage.AGENT_EXECUTION
        elif record.state is RunState.PREPARING_DATASET:
            stage = ErrorStage.DATASET_PREPARATION
        elif record.state is RunState.CREATED and stage is not ErrorStage.AGENT_RESOLUTION:
            stage = ErrorStage.REQUEST_VALIDATION

        return RunError(
            code="unexpected_runtime_error",
            message=f"Unexpected runtime error during {stage.value}",
            stage=stage,
            details={
                "run_id": run_id,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
        )

    def _cleanup_prepared_dataset(self, prepared_dataset: PreparedDataset | None) -> Exception | None:
        if prepared_dataset is None:
            return None

        close = getattr(prepared_dataset.duckdb_context, "close", None)
        if close is None or not callable(close):
            return None

        try:
            close()
        except Exception as exc:
            return exc

        return None
