from __future__ import annotations

from io import StringIO
from pathlib import Path

from agents.data_analyst import DataAnalystAgent
from interfaces.cli import execute_cli
from data import LocalDatasetPreparer
from runtime import AgentRegistry, RegisteredAgent, RuntimeCoordinator


def write_csv(path: Path) -> Path:
    path.write_text("store,sales,active\n1,100.5,true\n2,200.0,false\n", encoding="utf-8")
    return path


class FakeLLMAdapter:
    def generate(self, prompt: str) -> str:
        return "Resumen generado para la CLI"


def build_runtime_coordinator(artifacts_root: Path) -> RuntimeCoordinator:
    return RuntimeCoordinator(
        dataset_preparer=LocalDatasetPreparer(),
        agent_registry=AgentRegistry(
            {
                "data_analyst": RegisteredAgent(
                    agent_id="data_analyst",
                    executor=DataAnalystAgent(llm_adapter=FakeLLMAdapter()),
                    config={"model": "deepseek-r1:8b"},
                )
            }
        ),
        artifacts_root=artifacts_root,
    )


def test_execute_cli_renders_happy_path_with_traceable_outputs(repo_tmp_path: Path) -> None:
    dataset_path = write_csv(repo_tmp_path / "sample.csv")
    runtime = build_runtime_coordinator(repo_tmp_path / "artifacts")
    stdout = StringIO()
    stderr = StringIO()

    exit_code = execute_cli(
        [
            "--agent",
            "data_analyst",
            "--dataset",
            str(dataset_path),
            "--prompt",
            "Resume los hallazgos principales",
        ],
        stdout=stdout,
        stderr=stderr,
        runtime_coordinator=runtime,
    )

    output = stdout.getvalue()
    run_id = next(
        line.split(": ", maxsplit=1)[1]
        for line in output.splitlines()
        if line.startswith("Run ID: ")
    )
    record = runtime.tracker.get(run_id)

    assert exit_code == 0
    assert stderr.getvalue() == ""
    assert "Análisis completado" in output
    assert "Narrativa:" in output
    assert "Resumen generado para la CLI" in output
    assert "Hallazgos:" in output
    assert f"Session ID: {record.session_id}" in output
    assert f"Run ID: {run_id}" in output
    assert "Response artifact:" in output
    assert "Table artifacts:" in output
    assert record.result is not None
    assert record.result.artifact_manifest.response_path is not None
    assert Path(record.result.artifact_manifest.response_path).is_file()
    assert all(Path(path).is_file() for path in record.result.artifact_manifest.table_paths)


def test_execute_cli_supports_explicit_run_subcommand(repo_tmp_path: Path) -> None:
    dataset_path = write_csv(repo_tmp_path / "sample.csv")
    runtime = build_runtime_coordinator(repo_tmp_path / "artifacts")
    stdout = StringIO()
    stderr = StringIO()

    exit_code = execute_cli(
        [
            "run",
            "--agent",
            "data_analyst",
            "--dataset",
            str(dataset_path),
            "--prompt",
            "Resume los hallazgos principales",
        ],
        stdout=stdout,
        stderr=stderr,
        runtime_coordinator=runtime,
    )

    assert exit_code == 0
    assert stderr.getvalue() == ""
    assert "Análisis completado" in stdout.getvalue()


def test_execute_cli_renders_stable_error_for_unknown_agent(repo_tmp_path: Path) -> None:
    dataset_path = write_csv(repo_tmp_path / "sample.csv")
    runtime = build_runtime_coordinator(repo_tmp_path / "artifacts")
    stdout = StringIO()
    stderr = StringIO()

    exit_code = execute_cli(
        [
            "--agent",
            "unknown_agent",
            "--dataset",
            str(dataset_path),
            "--prompt",
            "Resume los hallazgos principales",
        ],
        stdout=stdout,
        stderr=stderr,
        runtime_coordinator=runtime,
    )

    error_output = stderr.getvalue()

    assert exit_code == 1
    assert stdout.getvalue() == ""
    assert "Error code: agent_not_found" in error_output
    assert "Stage: agent_resolution" in error_output
    assert "Message: Unknown agent_id: unknown_agent" in error_output
    assert "- available_agent_ids: ['data_analyst']" in error_output


def test_execute_cli_renders_stable_error_for_missing_dataset(repo_tmp_path: Path) -> None:
    runtime = build_runtime_coordinator(repo_tmp_path / "artifacts")
    stdout = StringIO()
    stderr = StringIO()

    exit_code = execute_cli(
        [
            "--agent",
            "data_analyst",
            "--dataset",
            str(repo_tmp_path / "missing.csv"),
            "--prompt",
            "Resume los hallazgos principales",
        ],
        stdout=stdout,
        stderr=stderr,
        runtime_coordinator=runtime,
    )

    error_output = stderr.getvalue()

    assert exit_code == 1
    assert stdout.getvalue() == ""
    assert "Error code: dataset_not_found" in error_output
    assert "Stage: dataset_preparation" in error_output
    assert "Message: Dataset path does not exist or is not a file" in error_output
    assert "- dataset_path:" in error_output


def test_execute_cli_reuses_explicit_session_id(repo_tmp_path: Path) -> None:
    dataset_path = write_csv(repo_tmp_path / "sample.csv")
    runtime = build_runtime_coordinator(repo_tmp_path / "artifacts")
    stdout = StringIO()
    stderr = StringIO()

    exit_code = execute_cli(
        [
            "--agent",
            "data_analyst",
            "--dataset",
            str(dataset_path),
            "--prompt",
            "Resume los hallazgos principales",
            "--session-id",
            "session-existing",
        ],
        stdout=stdout,
        stderr=stderr,
        runtime_coordinator=runtime,
    )

    output = stdout.getvalue()
    run_id = next(
        line.split(": ", maxsplit=1)[1]
        for line in output.splitlines()
        if line.startswith("Run ID: ")
    )
    record = runtime.tracker.get(run_id)

    assert exit_code == 0
    assert stderr.getvalue() == ""
    assert record.session_id == "session-existing"
    assert "Session ID: session-existing" in output
