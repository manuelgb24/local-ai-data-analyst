from pathlib import Path

import pytest

from application import (
    AgentExecutionContext,
    AgentResult,
    ArtifactManifest,
    DatasetColumn,
    DatasetProfile,
    ErrorStage,
    RunError,
    RunRequest,
    RunState,
)
from runtime import AgentRegistry, InMemoryRunTracker, PreparedDataset, RegisteredAgent, RuntimeCoordinator


class FakeClosableContext:
    def __init__(self, fail_on_close: bool = False) -> None:
        self.closed = False
        self.fail_on_close = fail_on_close

    def close(self) -> None:
        self.closed = True
        if self.fail_on_close:
            raise RuntimeError("close exploded")


def build_request(session_id: str | None = None) -> RunRequest:
    return RunRequest(
        agent_id="data_analyst",
        dataset_path="DatasetV1/Walmart_Sales.csv",
        user_prompt="Resume las ventas",
        session_id=session_id,
    )


def build_profile() -> DatasetProfile:
    return DatasetProfile(
        source_path="DatasetV1/Walmart_Sales.csv",
        format="csv",
        table_name="dataset_run_001",
        schema=[DatasetColumn(name="store", type="INTEGER")],
        row_count=3,
    )


def build_result(run_id: str) -> AgentResult:
    return AgentResult(
        narrative="Análisis completado",
        findings=["Hay datos disponibles"],
        sql_trace=[],
        tables=[],
        charts=[],
        artifact_manifest=ArtifactManifest(run_id=run_id),
    )


def build_registry(agent_executor) -> AgentRegistry:
    return AgentRegistry(
        {
            "data_analyst": RegisteredAgent(
                agent_id="data_analyst",
                executor=agent_executor,
                config={"model": "deepseek-r1:8b"},
            )
        }
    )


def test_tracker_generates_unique_run_and_session_ids_when_missing() -> None:
    tracker = InMemoryRunTracker()

    first = tracker.start_run(build_request())
    second = tracker.start_run(build_request())

    assert first.run_id.startswith("run-")
    assert first.session_id.startswith("session-")
    assert first.run_id != second.run_id
    assert first.session_id != second.session_id
    assert first.state is RunState.CREATED
    assert first.state_history == [RunState.CREATED]


def test_tracker_reuses_existing_session_id() -> None:
    tracker = InMemoryRunTracker()

    record = tracker.start_run(build_request(session_id="session-existing"))

    assert record.session_id == "session-existing"


def test_tracker_records_state_history_and_result_on_success() -> None:
    tracker = InMemoryRunTracker()
    record = tracker.start_run(build_request())

    tracker.mark_preparing_dataset(record.run_id)
    tracker.mark_running_agent(record.run_id)
    tracker.mark_succeeded(record.run_id, build_result(record.run_id))

    updated = tracker.get(record.run_id)
    assert updated.state_history == [
        RunState.CREATED,
        RunState.PREPARING_DATASET,
        RunState.RUNNING_AGENT,
        RunState.SUCCEEDED,
    ]
    assert updated.state is RunState.SUCCEEDED
    assert updated.result is not None
    assert updated.result.artifact_manifest.run_id == record.run_id


def test_tracker_records_run_error_on_failure() -> None:
    tracker = InMemoryRunTracker()
    record = tracker.start_run(build_request())
    error = RunError(
        code="dataset_not_found",
        message="No se encontró el dataset",
        stage=ErrorStage.DATASET_PREPARATION,
    )

    tracker.mark_preparing_dataset(record.run_id)
    tracker.mark_failed(record.run_id, error)

    updated = tracker.get(record.run_id)
    assert updated.state_history == [
        RunState.CREATED,
        RunState.PREPARING_DATASET,
        RunState.FAILED,
    ]
    assert updated.state is RunState.FAILED
    assert updated.error == error


def test_runtime_coordinator_wraps_unexpected_agent_exception_as_run_error(repo_tmp_path: Path) -> None:
    tracker = InMemoryRunTracker()
    context = FakeClosableContext()

    def fake_dataset_preparer(request: RunRequest, run_id: str) -> PreparedDataset:
        return PreparedDataset(dataset_profile=build_profile(), duckdb_context=context)

    def fake_agent_executor(request: RunRequest, context: AgentExecutionContext) -> AgentResult:
        raise RuntimeError("agent exploded")

    coordinator = RuntimeCoordinator(
        dataset_preparer=fake_dataset_preparer,
        agent_registry=build_registry(fake_agent_executor),
        tracker=tracker,
        artifacts_root=repo_tmp_path,
    )

    with pytest.raises(RunError, match="unexpected_runtime_error"):
        coordinator.run(build_request())

    run_id = next(iter({path.name for path in repo_tmp_path.iterdir() if path.is_dir()}))
    record = tracker.get(run_id)
    assert record.state is RunState.FAILED
    assert record.error is not None
    assert record.error.stage is ErrorStage.AGENT_EXECUTION
    assert record.error.details == {
        "category": "core",
        "run_id": run_id,
        "error_type": "RuntimeError",
        "error_message": "agent exploded",
    }
    assert context.closed is True


def test_runtime_coordinator_fails_unknown_agent_before_preparing_dataset(repo_tmp_path: Path) -> None:
    tracker = InMemoryRunTracker()
    dataset_preparer_called = False

    def fake_dataset_preparer(request: RunRequest, run_id: str) -> PreparedDataset:
        nonlocal dataset_preparer_called
        dataset_preparer_called = True
        return PreparedDataset(dataset_profile=build_profile(), duckdb_context={"run_id": run_id})

    coordinator = RuntimeCoordinator(
        dataset_preparer=fake_dataset_preparer,
        agent_registry=build_registry(lambda request, context: build_result(context.run_id)),
        tracker=tracker,
        artifacts_root=repo_tmp_path,
    )

    with pytest.raises(RunError, match="agent_not_found") as exc_info:
        coordinator.run(
            RunRequest(
                agent_id="unknown_agent",
                dataset_path="DatasetV1/Walmart_Sales.csv",
                user_prompt="Resume las ventas",
            )
        )

    run_id = next(iter(tracker._runs))
    record = tracker.get(run_id)

    assert dataset_preparer_called is False
    assert record.state is RunState.FAILED
    assert record.state_history == [RunState.CREATED, RunState.FAILED]
    assert record.error == exc_info.value
    assert exc_info.value.stage is ErrorStage.AGENT_RESOLUTION
    assert exc_info.value.details == {
        "category": "request",
        "agent_id": "unknown_agent",
        "available_agent_ids": ["data_analyst"],
    }


def test_runtime_coordinator_closes_context_on_success(repo_tmp_path: Path) -> None:
    tracker = InMemoryRunTracker()
    context = FakeClosableContext()

    def fake_dataset_preparer(request: RunRequest, run_id: str) -> PreparedDataset:
        return PreparedDataset(dataset_profile=build_profile(), duckdb_context=context)

    coordinator = RuntimeCoordinator(
        dataset_preparer=fake_dataset_preparer,
        agent_registry=build_registry(lambda request, agent_context: build_result(agent_context.run_id)),
        tracker=tracker,
        artifacts_root=repo_tmp_path,
    )

    result = coordinator.run(build_request())
    record = tracker.get(result.artifact_manifest.run_id)

    assert record.state is RunState.SUCCEEDED
    assert context.closed is True


def test_runtime_coordinator_does_not_replace_run_error_when_close_fails(repo_tmp_path: Path) -> None:
    tracker = InMemoryRunTracker()
    context = FakeClosableContext(fail_on_close=True)

    def fake_dataset_preparer(request: RunRequest, run_id: str) -> PreparedDataset:
        return PreparedDataset(dataset_profile=build_profile(), duckdb_context=context)

    def fake_agent_executor(request: RunRequest, agent_context: AgentExecutionContext) -> AgentResult:
        raise RunError(code="agent_failed", message="El agente falló", stage=ErrorStage.AGENT_EXECUTION)

    coordinator = RuntimeCoordinator(
        dataset_preparer=fake_dataset_preparer,
        agent_registry=build_registry(fake_agent_executor),
        tracker=tracker,
        artifacts_root=repo_tmp_path,
    )

    with pytest.raises(RunError, match="agent_failed") as exc_info:
        coordinator.run(build_request())

    record = tracker.get(next(iter(tracker._runs)))
    assert record.error == exc_info.value
    assert record.state is RunState.FAILED
    assert context.closed is True


def test_runtime_coordinator_fails_when_close_fails_after_success(repo_tmp_path: Path) -> None:
    tracker = InMemoryRunTracker()
    context = FakeClosableContext(fail_on_close=True)

    def fake_dataset_preparer(request: RunRequest, run_id: str) -> PreparedDataset:
        return PreparedDataset(dataset_profile=build_profile(), duckdb_context=context)

    coordinator = RuntimeCoordinator(
        dataset_preparer=fake_dataset_preparer,
        agent_registry=build_registry(lambda request, agent_context: build_result(agent_context.run_id)),
        tracker=tracker,
        artifacts_root=repo_tmp_path,
    )

    with pytest.raises(RunError, match="unexpected_runtime_error") as exc_info:
        coordinator.run(build_request())

    record = tracker.get(next(iter(tracker._runs)))
    assert record.state is RunState.FAILED
    assert record.error == exc_info.value
    assert record.error.stage is ErrorStage.AGENT_EXECUTION
    assert context.closed is True
