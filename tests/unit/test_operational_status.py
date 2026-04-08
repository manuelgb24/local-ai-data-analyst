from observability import AppConfig, ApplicationHealth, HealthStatus, ProveedorHealth, ReadinessReport


def test_app_config_normalizes_and_sorts_dataset_formats() -> None:
    config = AppConfig(
        default_agent_id="data_analyst",
        supported_dataset_formats=["Parquet", "csv", "XLSX", "csv"],
        proveedor_name="ollama",
        proveedor_endpoint="http://127.0.0.1:11434",
        required_model="deepseek-r1:8b",
    )

    assert config.supported_dataset_formats == ["csv", "parquet", "xlsx"]


def test_application_health_derives_error_status_when_any_check_fails() -> None:
    health = ApplicationHealth(
        ready=False,
        default_agent_id="data_analyst",
        artifacts_root="artifacts/runs",
        checks={"agent_registry": True, "artifacts_root_writable": False},
        details=["No se pudo escribir en artifacts."],
    )

    assert health.status is HealthStatus.ERROR
    assert health.checks["artifacts_root_writable"] is False


def test_provider_health_is_ready_only_when_binary_endpoint_and_model_are_available() -> None:
    health = ProveedorHealth(
        proveedor="ollama",
        endpoint="http://127.0.0.1:11434",
        reachable=True,
        model="deepseek-r1:8b",
        model_available=True,
        binary_available=True,
        version="0.6.0",
    )

    assert health.ready is True
    assert health.status is HealthStatus.OK


def test_readiness_report_aggregates_application_and_provider_state() -> None:
    report = ReadinessReport(
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

    assert report.ready is False
    assert report.status is HealthStatus.ERROR
    assert report.issues == ["Ollama no responde."]
