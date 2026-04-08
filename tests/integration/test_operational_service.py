from pathlib import Path

from application import GetAppConfigUseCase, GetOperationalStatusUseCase
from adapters import OllamaBinaryProbeResult, OllamaEndpointProbeResult, OllamaModelProbeResult
from observability import OperationalReadinessService
from runtime import AgentRegistry, RegisteredAgent


def build_registry() -> AgentRegistry:
    return AgentRegistry(
        {
            "data_analyst": RegisteredAgent(
                agent_id="data_analyst",
                executor=lambda request, context: None,
                config={"model": "deepseek-r1:8b"},
            )
        }
    )


def test_status_reports_not_ready_when_ollama_binary_and_endpoint_are_missing(repo_tmp_path: Path) -> None:
    service = OperationalReadinessService(
        agent_registry=build_registry(),
        artifacts_root=repo_tmp_path / "artifacts",
        binary_probe=lambda: OllamaBinaryProbeResult(available=False, detail="missing binary"),
        endpoint_probe=lambda endpoint, timeout: OllamaEndpointProbeResult(reachable=False, detail="endpoint down"),
        model_probe=lambda model, timeout: OllamaModelProbeResult(available=False, detail="missing model"),
    )

    report = GetOperationalStatusUseCase(service).execute()

    assert report.ready is False
    assert report.application.ready is True
    assert report.provider.binary_available is False
    assert report.provider.reachable is False
    assert report.provider.model_available is False
    assert "missing binary" in report.issues
    assert "endpoint down" in report.issues


def test_status_reports_application_error_when_artifacts_root_is_not_writable(repo_tmp_path: Path) -> None:
    blocked_path = repo_tmp_path / "artifacts-file"
    blocked_path.write_text("not-a-directory", encoding="utf-8")

    service = OperationalReadinessService(
        agent_registry=build_registry(),
        artifacts_root=blocked_path,
        binary_probe=lambda: OllamaBinaryProbeResult(available=True, path="C:/ollama.exe"),
        endpoint_probe=lambda endpoint, timeout: OllamaEndpointProbeResult(reachable=True, version="0.6.0"),
        model_probe=lambda model, timeout: OllamaModelProbeResult(available=True),
    )

    report = GetOperationalStatusUseCase(service).execute()

    assert report.ready is False
    assert report.application.ready is False
    assert report.provider.ready is True
    assert any("artifacts" in issue for issue in report.issues)


def test_status_reports_ready_when_all_checks_pass(repo_tmp_path: Path) -> None:
    service = OperationalReadinessService(
        agent_registry=build_registry(),
        artifacts_root=repo_tmp_path / "artifacts",
        binary_probe=lambda: OllamaBinaryProbeResult(available=True, path="C:/ollama.exe"),
        endpoint_probe=lambda endpoint, timeout: OllamaEndpointProbeResult(reachable=True, version="0.6.0"),
        model_probe=lambda model, timeout: OllamaModelProbeResult(available=True),
    )

    report = GetOperationalStatusUseCase(service).execute()

    assert report.ready is True
    assert report.issues == []
    assert report.provider.version == "0.6.0"
    assert report.application.checks["artifacts_root_writable"] is True


def test_config_use_case_returns_effective_local_defaults(repo_tmp_path: Path) -> None:
    service = OperationalReadinessService(
        agent_registry=build_registry(),
        artifacts_root=repo_tmp_path / "artifacts",
    )

    config = GetAppConfigUseCase(service).execute()

    assert config.default_agent_id == "data_analyst"
    assert config.supported_dataset_formats == ["csv", "parquet", "xlsx"]
    assert config.proveedor_name == "ollama"
    assert config.proveedor_endpoint == "http://127.0.0.1:11434"
    assert config.required_model == "deepseek-r1:8b"
