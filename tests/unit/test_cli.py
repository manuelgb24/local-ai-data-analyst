import argparse
from io import StringIO

import pytest

from application import ArtifactManifest, ErrorStage, RunError, TableResult
from interfaces.cli import execute_cli, build_run_request, render_config, render_error, render_status, render_success
from observability import (
    AppConfig,
    ApplicationHealth,
    ProveedorHealth,
    ReadinessReport,
    clear_context,
    configure_structured_logging,
)


class _ResultStub:
    def __init__(self) -> None:
        self.narrative = "Resumen final"
        self.findings = ["Hallazgo 1", "Hallazgo 2"]
        self.tables = [TableResult(name="preview", rows=[{"sales": 10}])]
        self.artifact_manifest = ArtifactManifest(
            run_id="run-123",
            response_path="artifacts/run-123/response.md",
            table_paths=["artifacts/run-123/tables/preview.json"],
            chart_paths=[],
        )


def test_build_run_request_translates_valid_cli_args() -> None:
    request = build_run_request(
        argparse.Namespace(
            agent_id="data_analyst",
            dataset_path="DatasetV1/demo_business_metrics.csv",
            user_prompt="Resume ventas",
            session_id="session-123",
        )
    )

    assert request.agent_id == "data_analyst"
    assert request.dataset_path == "DatasetV1/demo_business_metrics.csv"
    assert request.user_prompt == "Resume ventas"
    assert request.session_id == "session-123"


def test_build_run_request_wraps_contract_validation_as_run_error() -> None:
    with pytest.raises(RunError) as exc_info:
        build_run_request(
            argparse.Namespace(
                agent_id="data_analyst",
                dataset_path="DatasetV1/demo_business_metrics.txt",
                user_prompt="Resume ventas",
                session_id=None,
            )
        )

    assert exc_info.value.code == "invalid_request"
    assert exc_info.value.stage is ErrorStage.REQUEST_VALIDATION
    assert "supported format" in exc_info.value.message


def test_render_success_includes_human_summary_and_artifact_paths() -> None:
    output = render_success(_ResultStub(), session_id="session-123")

    assert "Análisis completado" in output
    assert "Narrativa:" in output
    assert "Resumen final" in output
    assert "Hallazgos:" in output
    assert "- Hallazgo 1" in output
    assert "Session ID: session-123" in output
    assert "Run ID: run-123" in output
    assert "Response artifact: artifacts/run-123/response.md" in output
    assert "Table artifacts:" in output
    assert "- artifacts/run-123/tables/preview.json" in output


def test_render_error_includes_sorted_details() -> None:
    output = render_error(
        RunError(
            code="dataset_not_found",
            message="Dataset path does not exist or is not a file",
            stage=ErrorStage.DATASET_PREPARATION,
            details={"z_key": "last", "a_key": "first"},
        )
    )

    assert "Error code: dataset_not_found" in output
    assert "Stage: dataset_preparation" in output
    assert "Message: Dataset path does not exist or is not a file" in output
    assert output.index("- a_key: first") < output.index("- z_key: last")


def test_render_status_includes_actionable_issues_in_human_mode() -> None:
    output = render_status(
        ReadinessReport(
            application=ApplicationHealth(
                ready=True,
                default_agent_id="data_analyst",
                artifacts_root="artifacts/runs",
                checks={"agent_registry": True, "artifacts_root_writable": True, "config_available": True},
            ),
            provider=ProveedorHealth(
                proveedor="ollama",
                endpoint="http://127.0.0.1:11434",
                reachable=False,
                model="deepseek-r1:8b",
                model_available=False,
                binary_available=True,
                details=["Ollama no responde."],
            ),
            issues=["Ollama no responde."],
        )
    )

    assert "System ready: no" in output
    assert "Application health:" in output
    assert "Provider health:" in output
    assert "Actionable issues:" in output
    assert "- Ollama no responde." in output


def test_render_config_supports_json_output() -> None:
    output = render_config(
        AppConfig(
            default_agent_id="data_analyst",
            supported_dataset_formats=["csv", "xlsx", "parquet"],
            proveedor_name="ollama",
            proveedor_endpoint="http://127.0.0.1:11434",
            required_model="deepseek-r1:8b",
        ),
        json_output=True,
    )

    assert '"default_agent_id": "data_analyst"' in output
    assert '"proveedor_name": "ollama"' in output


def test_execute_cli_status_returns_non_zero_when_system_is_not_ready(repo_tmp_path) -> None:
    class _StubReadinessService:
        def get_readiness_report(self) -> ReadinessReport:
            return ReadinessReport(
                application=ApplicationHealth(
                    ready=True,
                    default_agent_id="data_analyst",
                    artifacts_root=str(repo_tmp_path / "artifacts"),
                    checks={"agent_registry": True, "artifacts_root_writable": True, "config_available": True},
                ),
                provider=ProveedorHealth(
                    proveedor="ollama",
                    endpoint="http://127.0.0.1:11434",
                    reachable=False,
                    model="deepseek-r1:8b",
                    model_available=False,
                    binary_available=True,
                    details=["Ollama no responde."],
                ),
                issues=["Ollama no responde."],
            )

        def get_app_config(self) -> AppConfig:
            raise AssertionError("config should not be called in this test")

    stdout = StringIO()
    stderr = StringIO()

    exit_code = execute_cli(
        ["status", "--json"],
        stdout=stdout,
        stderr=stderr,
        operational_readiness_service=_StubReadinessService(),
    )

    assert exit_code == 1
    assert stderr.getvalue() == ""
    assert '"ready": false' in stdout.getvalue()


def test_execute_cli_config_renders_human_readable_output() -> None:
    class _StubReadinessService:
        def get_readiness_report(self) -> ReadinessReport:
            raise AssertionError("status should not be called in this test")

        def get_app_config(self) -> AppConfig:
            return AppConfig(
                default_agent_id="data_analyst",
                supported_dataset_formats=["csv", "xlsx", "parquet"],
                proveedor_name="ollama",
                proveedor_endpoint="http://127.0.0.1:11434",
                required_model="deepseek-r1:8b",
            )

    stdout = StringIO()
    stderr = StringIO()

    exit_code = execute_cli(
        ["config"],
        stdout=stdout,
        stderr=stderr,
        operational_readiness_service=_StubReadinessService(),
    )

    assert exit_code == 0
    assert stderr.getvalue() == ""
    assert "Effective config:" in stdout.getvalue()
    assert "- required_model: deepseek-r1:8b" in stdout.getvalue()


def test_execute_cli_logs_to_structured_stream_without_polluting_human_output(repo_tmp_path) -> None:
    class _StubReadinessService:
        def get_readiness_report(self) -> ReadinessReport:
            return ReadinessReport(
                application=ApplicationHealth(
                    ready=True,
                    default_agent_id="data_analyst",
                    artifacts_root=str(repo_tmp_path / "artifacts"),
                    checks={"agent_registry": True, "artifacts_root_writable": True, "config_available": True},
                ),
                provider=ProveedorHealth(
                    proveedor="ollama",
                    endpoint="http://127.0.0.1:11434",
                    reachable=True,
                    model="deepseek-r1:8b",
                    model_available=True,
                    binary_available=True,
                    details=[],
                ),
                issues=[],
            )

        def get_app_config(self) -> AppConfig:
            raise AssertionError("config should not be called in this test")

    log_stream = StringIO()
    stdout = StringIO()
    stderr = StringIO()
    clear_context()
    configure_structured_logging(stream=log_stream, force=True)

    exit_code = execute_cli(
        ["status", "--json"],
        stdout=stdout,
        stderr=stderr,
        operational_readiness_service=_StubReadinessService(),
    )

    assert exit_code == 0
    assert stderr.getvalue() == ""
    assert '"ready": true' in stdout.getvalue()
    assert '"event": "command_started"' in log_stream.getvalue()
    assert '"event": "request_completed"' in log_stream.getvalue()
