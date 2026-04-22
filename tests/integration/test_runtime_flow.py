import json
from io import StringIO
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
    RunAnalysisUseCase,
)
from data import PreparedDataset
from observability import bind_context, clear_context, configure_structured_logging, reset_context
from runtime import AgentRegistry, InMemoryRunTracker, RegisteredAgent, RuntimeCoordinator


def build_request(session_id: str | None = None) -> RunRequest:
    return RunRequest(
        agent_id="data_analyst",
        dataset_path="DatasetV1/demo_business_metrics.csv",
        user_prompt="Resume las ventas",
        session_id=session_id,
    )


def build_profile() -> DatasetProfile:
    return DatasetProfile(
        source_path="DatasetV1/demo_business_metrics.csv",
        format="csv",
        table_name="dataset_run_001",
        schema=[DatasetColumn(name="store", type="INTEGER")],
        row_count=3,
    )


def build_result(run_id: str) -> AgentResult:
    return AgentResult(
        narrative="Análisis completado",
        findings=["Las ventas son estables"],
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


def parse_log_lines(stream: StringIO) -> list[dict[str, object]]:
    return [json.loads(line) for line in stream.getvalue().splitlines() if line.strip()]


def test_run_analysis_use_case_executes_happy_path_with_context_and_tracking(repo_tmp_path: Path) -> None:
    tracker = InMemoryRunTracker()
    observed: dict[str, object] = {}

    def fake_dataset_preparer(request: RunRequest, run_id: str) -> PreparedDataset:
        observed["dataset_request"] = request
        observed["prepared_run_id"] = run_id
        return PreparedDataset(
            dataset_profile=build_profile(),
            duckdb_context={"connection": "fake", "run_id": run_id},
        )

    def fake_agent_executor(request: RunRequest, context: AgentExecutionContext) -> AgentResult:
        observed["agent_request"] = request
        observed["context"] = context
        return build_result(context.run_id)

    coordinator = RuntimeCoordinator(
        dataset_preparer=fake_dataset_preparer,
        agent_registry=build_registry(fake_agent_executor),
        tracker=tracker,
        artifacts_root=repo_tmp_path,
    )
    use_case = RunAnalysisUseCase(runtime=coordinator)

    result = use_case.execute(build_request())
    record = tracker.get(result.artifact_manifest.run_id)
    context = observed["context"]

    assert isinstance(context, AgentExecutionContext)
    assert record.state is RunState.SUCCEEDED
    assert record.state_history == [
        RunState.CREATED,
        RunState.PREPARING_DATASET,
        RunState.RUNNING_AGENT,
        RunState.SUCCEEDED,
    ]
    assert record.session_id.startswith("session-")
    assert context.run_id == result.artifact_manifest.run_id
    assert context.session_id == record.session_id
    assert context.dataset_profile.table_name == "dataset_run_001"
    assert context.duckdb_context == {"connection": "fake", "run_id": context.run_id}
    assert context.output_dir == str(repo_tmp_path / context.run_id)
    assert Path(context.output_dir).is_dir()
    assert result.artifact_manifest.response_path is not None
    assert Path(result.artifact_manifest.response_path).is_file()
    assert result.artifact_manifest.table_paths == []
    assert result.artifact_manifest.chart_paths == []


def test_runtime_marks_failed_when_dataset_preparation_raises_run_error(repo_tmp_path: Path) -> None:
    tracker = InMemoryRunTracker()
    captured_run_id: dict[str, str] = {}

    def fake_dataset_preparer(request: RunRequest, run_id: str) -> PreparedDataset:
        captured_run_id["value"] = run_id
        raise RunError(
            code="dataset_not_found",
            message="No se encontró el dataset",
            stage=ErrorStage.DATASET_PREPARATION,
        )

    def fake_agent_executor(request: RunRequest, context: AgentExecutionContext) -> AgentResult:
        raise AssertionError("agent executor should not be called")

    use_case = RunAnalysisUseCase(
        runtime=RuntimeCoordinator(
            dataset_preparer=fake_dataset_preparer,
            agent_registry=build_registry(fake_agent_executor),
            tracker=tracker,
            artifacts_root=repo_tmp_path,
        )
    )

    with pytest.raises(RunError, match="dataset_not_found"):
        use_case.execute(build_request())

    record = tracker.get(captured_run_id["value"])
    assert record.state is RunState.FAILED
    assert record.error is not None
    assert record.error.code == "dataset_not_found"
    assert record.state_history == [
        RunState.CREATED,
        RunState.PREPARING_DATASET,
        RunState.FAILED,
    ]


def test_runtime_marks_failed_when_agent_execution_raises_run_error(repo_tmp_path: Path) -> None:
    tracker = InMemoryRunTracker()
    captured_run_id: dict[str, str] = {}

    def fake_dataset_preparer(request: RunRequest, run_id: str) -> PreparedDataset:
        return PreparedDataset(dataset_profile=build_profile(), duckdb_context={"run_id": run_id})

    def fake_agent_executor(request: RunRequest, context: AgentExecutionContext) -> AgentResult:
        captured_run_id["value"] = context.run_id
        raise RunError(
            code="agent_failed",
            message="El agente falló",
            stage=ErrorStage.AGENT_EXECUTION,
        )

    use_case = RunAnalysisUseCase(
        runtime=RuntimeCoordinator(
            dataset_preparer=fake_dataset_preparer,
            agent_registry=build_registry(fake_agent_executor),
            tracker=tracker,
            artifacts_root=repo_tmp_path,
        )
    )

    with pytest.raises(RunError, match="agent_failed"):
        use_case.execute(build_request(session_id="session-existing"))

    record = tracker.get(captured_run_id["value"])
    assert record.session_id == "session-existing"
    assert record.state is RunState.FAILED
    assert record.error is not None
    assert record.error.stage is ErrorStage.AGENT_EXECUTION
    assert record.state_history == [
        RunState.CREATED,
        RunState.PREPARING_DATASET,
        RunState.RUNNING_AGENT,
        RunState.FAILED,
    ]


def test_runtime_logs_correlated_trace_session_and_run_ids(repo_tmp_path: Path) -> None:
    tracker = InMemoryRunTracker()
    log_stream = StringIO()
    clear_context()
    configure_structured_logging(stream=log_stream, force=True)

    def fake_dataset_preparer(request: RunRequest, run_id: str) -> PreparedDataset:
        return PreparedDataset(
            dataset_profile=build_profile(),
            duckdb_context={"connection": "fake", "run_id": run_id},
        )

    def fake_agent_executor(request: RunRequest, context: AgentExecutionContext) -> AgentResult:
        return build_result(context.run_id)

    use_case = RunAnalysisUseCase(
        runtime=RuntimeCoordinator(
            dataset_preparer=fake_dataset_preparer,
            agent_registry=build_registry(fake_agent_executor),
            tracker=tracker,
            artifacts_root=repo_tmp_path,
        )
    )

    token = bind_context(trace_id="trace-runtime-123")
    try:
        result = use_case.execute(build_request(session_id="session-existing"))
    finally:
        reset_context(token)
        clear_context()

    record = tracker.get(result.artifact_manifest.run_id)
    payloads = parse_log_lines(log_stream)
    run_started = next(item for item in payloads if item["event"] == "run_started")
    dataset_preparing = next(item for item in payloads if item["event"] == "dataset_preparing")
    run_succeeded = next(item for item in payloads if item["event"] == "run_succeeded")

    assert run_started["trace_id"] == "trace-runtime-123"
    assert run_started["session_id"] == "session-existing"
    assert run_started["run_id"] == record.run_id
    assert dataset_preparing["trace_id"] == "trace-runtime-123"
    assert dataset_preparing["run_id"] == record.run_id
    assert run_succeeded["trace_id"] == "trace-runtime-123"
    assert run_succeeded["session_id"] == "session-existing"
    assert run_succeeded["run_id"] == record.run_id


def test_runtime_adds_category_to_persisted_failures(repo_tmp_path: Path) -> None:
    tracker = InMemoryRunTracker()
    captured_run_id: dict[str, str] = {}

    def fake_dataset_preparer(request: RunRequest, run_id: str) -> PreparedDataset:
        captured_run_id["value"] = run_id
        raise RunError(
            code="dataset_not_found",
            message="No se encontró el dataset",
            stage=ErrorStage.DATASET_PREPARATION,
        )

    use_case = RunAnalysisUseCase(
        runtime=RuntimeCoordinator(
            dataset_preparer=fake_dataset_preparer,
            agent_registry=build_registry(lambda request, context: build_result(context.run_id)),
            tracker=tracker,
            artifacts_root=repo_tmp_path,
        )
    )

    with pytest.raises(RunError):
        use_case.execute(build_request())

    record = tracker.get(captured_run_id["value"])
    assert record.error is not None
    assert record.error.details == {"category": "dataset"}
