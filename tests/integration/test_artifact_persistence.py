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
    TableResult,
)
from data import PreparedDataset
from runtime import AgentRegistry, InMemoryRunTracker, RegisteredAgent, RuntimeCoordinator


def build_request() -> RunRequest:
    return RunRequest(
        agent_id="data_analyst",
        dataset_path="DatasetV1/Walmart_Sales.csv",
        user_prompt="Resume ventas",
    )


def build_profile() -> DatasetProfile:
    return DatasetProfile(
        source_path="DatasetV1/Walmart_Sales.csv",
        format="csv",
        table_name="dataset_run_001",
        schema=[DatasetColumn(name="store", type="INTEGER")],
        row_count=3,
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


def test_runtime_coordinator_persists_response_and_tables(repo_tmp_path: Path) -> None:
    tracker = InMemoryRunTracker()

    def fake_dataset_preparer(request: RunRequest, run_id: str) -> PreparedDataset:
        return PreparedDataset(
            dataset_profile=build_profile(),
            duckdb_context={"connection": "fake", "run_id": run_id},
        )

    def fake_agent_executor(request: RunRequest, context: AgentExecutionContext) -> AgentResult:
        return AgentResult(
            narrative="Narrativa final",
            findings=["Hallazgo principal"],
            sql_trace=[],
            tables=[TableResult(name="preview", rows=[{"store": 1}])],
            charts=[],
            artifact_manifest=ArtifactManifest(run_id=context.run_id),
        )

    coordinator = RuntimeCoordinator(
        dataset_preparer=fake_dataset_preparer,
        agent_registry=build_registry(fake_agent_executor),
        tracker=tracker,
        artifacts_root=repo_tmp_path / "artifacts",
    )

    result = coordinator.run(build_request())

    response_path = Path(result.artifact_manifest.response_path or "")
    assert response_path.is_file()
    assert response_path.read_text(encoding="utf-8").startswith("# Narrative")
    assert len(result.artifact_manifest.table_paths) == 1
    assert Path(result.artifact_manifest.table_paths[0]).is_file()
    assert tracker.get(result.artifact_manifest.run_id).result == result


def test_runtime_coordinator_marks_failed_when_artifact_persistence_raises(repo_tmp_path: Path) -> None:
    tracker = InMemoryRunTracker()
    captured_run_id: dict[str, str] = {}

    def fake_dataset_preparer(request: RunRequest, run_id: str) -> PreparedDataset:
        return PreparedDataset(
            dataset_profile=build_profile(),
            duckdb_context={"connection": "fake", "run_id": run_id},
        )

    def fake_agent_executor(request: RunRequest, context: AgentExecutionContext) -> AgentResult:
        captured_run_id["value"] = context.run_id
        return AgentResult(
            narrative="Narrativa final",
            findings=["Hallazgo principal"],
            sql_trace=[],
            tables=[],
            charts=[],
            artifact_manifest=ArtifactManifest(run_id=context.run_id),
        )

    def failing_artifact_persister(result: AgentResult, output_dir: str | Path) -> ArtifactManifest:
        raise RuntimeError("disk exploded")

    coordinator = RuntimeCoordinator(
        dataset_preparer=fake_dataset_preparer,
        agent_registry=build_registry(fake_agent_executor),
        tracker=tracker,
        artifact_persister=failing_artifact_persister,
        artifacts_root=repo_tmp_path / "artifacts",
    )

    with pytest.raises(RunError, match="artifact_persistence_failed") as exc_info:
        coordinator.run(build_request())

    record = tracker.get(captured_run_id["value"])
    assert record.state.value == "failed"
    assert record.error == exc_info.value
    assert exc_info.value.stage is ErrorStage.ARTIFACT_PERSISTENCE
