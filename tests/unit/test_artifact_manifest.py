import json
from pathlib import Path

import pytest

from application import AgentResult, ArtifactManifest, ChartReference, ErrorStage, RunError, TableResult
from artifacts import FilesystemArtifactPersister


def build_result(*, chart_path: str | None = None) -> AgentResult:
    charts = []
    if chart_path is not None:
        charts.append(ChartReference(name="sales-chart", path=chart_path))

    return AgentResult(
        narrative="Narrativa persistida",
        findings=["Hallazgo 1", "Hallazgo 2"],
        sql_trace=[],
        tables=[
            TableResult(name="preview", rows=[{"store": 1, "sales": 100.0}]),
            TableResult(name="numeric_summary", rows=[{"column_name": "sales", "avg_value": 100.0}]),
        ],
        charts=charts,
        recommendations=["Revisar la tendencia semanal"],
        artifact_manifest=ArtifactManifest(run_id="run-123"),
    )


def test_filesystem_artifact_persister_writes_response_tables_and_copied_charts(
    repo_tmp_path: Path,
) -> None:
    output_dir = repo_tmp_path / "artifacts" / "run-123"
    source_chart = repo_tmp_path / "source-chart.png"
    source_chart.write_bytes(b"fake-png-data")

    manifest = FilesystemArtifactPersister()(build_result(chart_path=str(source_chart)), output_dir)

    response_path = Path(manifest.response_path or "")
    assert manifest.run_id == "run-123"
    assert response_path.is_file()
    assert response_path.read_text(encoding="utf-8").startswith("# Narrative")

    assert len(manifest.table_paths) == 2
    preview_export = Path(manifest.table_paths[0])
    assert preview_export.is_file()
    assert json.loads(preview_export.read_text(encoding="utf-8")) == [{"store": 1, "sales": 100.0}]

    assert len(manifest.chart_paths) == 1
    copied_chart = Path(manifest.chart_paths[0])
    assert copied_chart.is_file()
    assert copied_chart.read_bytes() == b"fake-png-data"


def test_filesystem_artifact_persister_fails_when_chart_source_does_not_exist(repo_tmp_path: Path) -> None:
    output_dir = repo_tmp_path / "artifacts" / "run-123"

    with pytest.raises(RunError) as exc_info:
        FilesystemArtifactPersister()(
            build_result(chart_path=str(repo_tmp_path / "missing-chart.png")),
            output_dir,
        )

    assert exc_info.value.code == "artifact_chart_source_missing"
    assert exc_info.value.stage is ErrorStage.ARTIFACT_PERSISTENCE
