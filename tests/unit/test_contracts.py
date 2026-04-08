import pytest

from application.contracts import (
    AgentExecutionContext,
    AgentResult,
    ArtifactManifest,
    ChartReference,
    DatasetColumn,
    DatasetProfile,
    RunRequest,
    SqlTraceEntry,
    TableResult,
)


def build_dataset_profile() -> DatasetProfile:
    return DatasetProfile(
        source_path="tests/fixtures/sample.csv",
        format="csv",
        table_name="dataset_run_001",
        schema=[DatasetColumn(name="store", type="INTEGER")],
        row_count=3,
    )


def test_run_request_accepts_valid_local_request() -> None:
    request = RunRequest(
        agent_id="data_analyst",
        dataset_path="DatasetV1/Walmart_Sales.csv",
        user_prompt="Resume las ventas",
        session_id="session-123",
    )

    assert request.agent_id == "data_analyst"
    assert request.dataset_path == "DatasetV1/Walmart_Sales.csv"
    assert request.user_prompt == "Resume las ventas"
    assert request.session_id == "session-123"


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("agent_id", {"agent_id": ""}),
        ("user_prompt", {"user_prompt": "   "}),
        ("dataset_path", {"dataset_path": "https://example.com/dataset.csv"}),
    ],
    ids=["empty-agent-id", "empty-user-prompt", "dataset-path-is-url"],
)
def test_run_request_rejects_invalid_inputs(field_name: str, kwargs: dict[str, str]) -> None:
    payload = {
        "agent_id": "data_analyst",
        "dataset_path": "DatasetV1/Walmart_Sales.csv",
        "user_prompt": "Resume las ventas",
    }
    payload.update(kwargs)

    with pytest.raises((TypeError, ValueError), match=field_name):
        RunRequest(**payload)


def test_dataset_profile_accepts_supported_format_and_schema() -> None:
    profile = build_dataset_profile()

    assert profile.format == "csv"
    assert profile.row_count == 3
    assert profile.schema[0].name == "store"


def test_dataset_profile_rejects_unsupported_format() -> None:
    with pytest.raises(ValueError, match="format"):
        DatasetProfile(
            source_path="tests/fixtures/sample.json",
            format="json",
            table_name="dataset_run_001",
            schema=[DatasetColumn(name="store", type="INTEGER")],
            row_count=3,
        )


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("run_id", {"run_id": ""}),
        ("session_id", {"session_id": "   "}),
        ("output_dir", {"output_dir": ""}),
    ],
    ids=["empty-run-id", "empty-session-id", "empty-output-dir"],
)
def test_agent_execution_context_requires_core_identifiers(
    field_name: str, kwargs: dict[str, str]
) -> None:
    payload = {
        "run_id": "run-123",
        "session_id": "session-123",
        "dataset_profile": build_dataset_profile(),
        "duckdb_context": object(),
        "output_dir": "artifacts/run-123",
    }
    payload.update(kwargs)

    with pytest.raises((TypeError, ValueError), match=field_name):
        AgentExecutionContext(**payload)


def test_agent_result_accepts_empty_collections_when_manifest_exists() -> None:
    result = AgentResult(
        narrative="Análisis completado",
        findings=[],
        sql_trace=[],
        tables=[],
        charts=[],
        artifact_manifest=ArtifactManifest(run_id="run-123"),
    )

    assert result.findings == []
    assert result.sql_trace == []
    assert result.tables == []
    assert result.charts == []
    assert result.artifact_manifest.run_id == "run-123"


def test_agent_result_requires_artifact_manifest() -> None:
    with pytest.raises(TypeError, match="artifact_manifest"):
        AgentResult(
            narrative="Análisis completado",
            findings=[],
            sql_trace=[],
            tables=[],
            charts=[],
        )


def test_artifact_manifest_accepts_empty_paths_lists() -> None:
    manifest = ArtifactManifest(run_id="run-123", table_paths=[], chart_paths=[])

    assert manifest.run_id == "run-123"
    assert manifest.table_paths == []
    assert manifest.chart_paths == []


def test_artifact_manifest_rejects_empty_run_id() -> None:
    with pytest.raises(ValueError, match="run_id"):
        ArtifactManifest(run_id="")


def test_supporting_contract_helpers_accept_valid_values() -> None:
    sql_entry = SqlTraceEntry(statement="SELECT 1", status="ok", rows_returned=1)
    table = TableResult(name="summary", rows=[{"sales": 10}])
    chart = ChartReference(name="sales-by-store", path="artifacts/run-123/chart.png")

    assert sql_entry.status.value == "ok"
    assert table.rows == [{"sales": 10}]
    assert chart.path == "artifacts/run-123/chart.png"
