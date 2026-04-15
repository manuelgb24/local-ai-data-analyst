from pathlib import Path

from fastapi.testclient import TestClient

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
from artifacts import FilesystemRunMetadataStore, RUN_METADATA_FILENAME
from data import PreparedDataset
from interfaces.api import create_app
from observability import ApplicationHealth, ProveedorHealth
from runtime import AgentRegistry, InMemoryRunTracker, RegisteredAgent, RuntimeCoordinator


def build_profile() -> DatasetProfile:
    return DatasetProfile(
        source_path="DatasetV1/Walmart_Sales.csv",
        format="csv",
        table_name="dataset_run_api_001",
        schema=[DatasetColumn(name="sales", type="DOUBLE")],
        row_count=2,
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


def build_runtime(
    *,
    artifacts_root: Path,
    store: FilesystemRunMetadataStore,
    agent_executor,
) -> RuntimeCoordinator:
    def fake_dataset_preparer(request: RunRequest, run_id: str) -> PreparedDataset:
        return PreparedDataset(
            dataset_profile=build_profile(),
            duckdb_context={"run_id": run_id},
        )

    return RuntimeCoordinator(
        dataset_preparer=fake_dataset_preparer,
        agent_registry=build_registry(agent_executor),
        tracker=InMemoryRunTracker(on_change=store.save),
        artifacts_root=artifacts_root,
    )


class StubReadinessService:
    def __init__(self, artifacts_root: Path) -> None:
        self._artifacts_root = artifacts_root

    def get_application_health(self) -> ApplicationHealth:
        return ApplicationHealth(
            ready=True,
            default_agent_id="data_analyst",
            artifacts_root=str(self._artifacts_root),
            checks={"agent_registry": True, "artifacts_root_writable": True, "config_available": True},
        )

    def get_provider_health(self) -> ProveedorHealth:
        return ProveedorHealth(
            proveedor="ollama",
            endpoint="http://127.0.0.1:11434",
            reachable=True,
            model="deepseek-r1:8b",
            model_available=True,
            binary_available=True,
            binary_path="C:/ollama.exe",
            version="0.6.0",
        )


def test_post_runs_executes_core_and_persists_detail(repo_tmp_path: Path) -> None:
    artifacts_root = repo_tmp_path / "artifacts"
    store = FilesystemRunMetadataStore(artifacts_root=artifacts_root)

    def fake_agent_executor(request: RunRequest, context: AgentExecutionContext) -> AgentResult:
        return AgentResult(
            narrative="Narrativa API",
            findings=["Hallazgo API"],
            sql_trace=[],
            tables=[TableResult(name="preview", rows=[{"sales": 10.5}])],
            charts=[],
            artifact_manifest=ArtifactManifest(run_id=context.run_id),
        )

    client = TestClient(
        create_app(
            artifacts_root=artifacts_root,
            runtime_coordinator=build_runtime(
                artifacts_root=artifacts_root,
                store=store,
                agent_executor=fake_agent_executor,
            ),
            operational_readiness_service=StubReadinessService(artifacts_root),
            run_metadata_store=store,
        )
    )

    response = client.post(
        "/runs",
        json={
            "agent_id": "data_analyst",
            "dataset_path": "DatasetV1/Walmart_Sales.csv",
            "user_prompt": "Resume ventas",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    run_id = payload["run_id"]

    assert payload["agent_id"] == "data_analyst"
    assert payload["status"] == "succeeded"
    assert payload["dataset_profile"]["table_name"] == "dataset_run_api_001"
    assert payload["result"]["narrative"] == "Narrativa API"
    assert payload["artifact_manifest"]["run_id"] == run_id
    assert (artifacts_root / run_id / RUN_METADATA_FILENAME).is_file()


def test_post_runs_with_invalid_payload_returns_api_error_shape(repo_tmp_path: Path) -> None:
    artifacts_root = repo_tmp_path / "artifacts"
    store = FilesystemRunMetadataStore(artifacts_root=artifacts_root)

    client = TestClient(
        create_app(
            artifacts_root=artifacts_root,
            runtime_coordinator=build_runtime(
                artifacts_root=artifacts_root,
                store=store,
                agent_executor=lambda request, context: AgentResult(
                    narrative="unused",
                    findings=[],
                    sql_trace=[],
                    tables=[],
                    charts=[],
                    artifact_manifest=ArtifactManifest(run_id=context.run_id),
                ),
            ),
            operational_readiness_service=StubReadinessService(artifacts_root),
            run_metadata_store=store,
        )
    )

    response = client.post(
        "/runs",
        json={
            "agent_id": "data_analyst",
            "dataset_path": "DatasetV1/Walmart_Sales.txt",
            "user_prompt": "Resume ventas",
        },
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "invalid_request"
    assert payload["status"] == 400
    assert payload["details"]["stage"] == "request_validation"
    assert payload["trace_id"]


def test_health_endpoints_reuse_operational_shapes(repo_tmp_path: Path) -> None:
    artifacts_root = repo_tmp_path / "artifacts"
    store = FilesystemRunMetadataStore(artifacts_root=artifacts_root)
    client = TestClient(
        create_app(
            artifacts_root=artifacts_root,
            runtime_coordinator=build_runtime(
                artifacts_root=artifacts_root,
                store=store,
                agent_executor=lambda request, context: AgentResult(
                    narrative="unused",
                    findings=[],
                    sql_trace=[],
                    tables=[],
                    charts=[],
                    artifact_manifest=ArtifactManifest(run_id=context.run_id),
                ),
            ),
            operational_readiness_service=StubReadinessService(artifacts_root),
            run_metadata_store=store,
        )
    )

    response = client.get("/health")
    provider_response = client.get("/health/proveedor")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["artifacts_root"] == str(artifacts_root)
    assert provider_response.status_code == 200
    assert provider_response.json()["proveedor"] == "ollama"
    assert provider_response.json()["model_available"] is True


def test_get_runs_returns_empty_list_when_no_metadata_exists(repo_tmp_path: Path) -> None:
    artifacts_root = repo_tmp_path / "artifacts"
    store = FilesystemRunMetadataStore(artifacts_root=artifacts_root)
    client = TestClient(
        create_app(
            artifacts_root=artifacts_root,
            runtime_coordinator=build_runtime(
                artifacts_root=artifacts_root,
                store=store,
                agent_executor=lambda request, context: AgentResult(
                    narrative="unused",
                    findings=[],
                    sql_trace=[],
                    tables=[],
                    charts=[],
                    artifact_manifest=ArtifactManifest(run_id=context.run_id),
                ),
            ),
            operational_readiness_service=StubReadinessService(artifacts_root),
            run_metadata_store=store,
        )
    )

    response = client.get("/runs")

    assert response.status_code == 200
    assert response.json() == []


def test_get_runs_and_artifacts_read_persisted_history_after_app_recreation(repo_tmp_path: Path) -> None:
    artifacts_root = repo_tmp_path / "artifacts"
    store = FilesystemRunMetadataStore(artifacts_root=artifacts_root)

    def fake_agent_executor(request: RunRequest, context: AgentExecutionContext) -> AgentResult:
        return AgentResult(
            narrative="Narrativa persistida",
            findings=["Hallazgo persistido"],
            sql_trace=[],
            tables=[TableResult(name="preview", rows=[{"sales": 10.5}])],
            charts=[],
            artifact_manifest=ArtifactManifest(run_id=context.run_id),
        )

    app = create_app(
        artifacts_root=artifacts_root,
        runtime_coordinator=build_runtime(
            artifacts_root=artifacts_root,
            store=store,
            agent_executor=fake_agent_executor,
        ),
        operational_readiness_service=StubReadinessService(artifacts_root),
        run_metadata_store=store,
    )
    client = TestClient(app)
    post_response = client.post(
        "/runs",
        json={
            "agent_id": "data_analyst",
            "dataset_path": "DatasetV1/Walmart_Sales.csv",
            "user_prompt": "Resume ventas",
        },
    )
    run_id = post_response.json()["run_id"]

    recreated_client = TestClient(
        create_app(
            artifacts_root=artifacts_root,
            runtime_coordinator=build_runtime(
                artifacts_root=artifacts_root,
                store=FilesystemRunMetadataStore(artifacts_root=artifacts_root),
                agent_executor=fake_agent_executor,
            ),
            operational_readiness_service=StubReadinessService(artifacts_root),
            run_metadata_store=FilesystemRunMetadataStore(artifacts_root=artifacts_root),
        )
    )

    list_response = recreated_client.get("/runs")
    detail_response = recreated_client.get(f"/runs/{run_id}")
    artifacts_response = recreated_client.get(f"/runs/{run_id}/artifacts")

    assert list_response.status_code == 200
    assert list_response.json()[0]["run_id"] == run_id
    assert list_response.json()[0]["dataset_path"] == "DatasetV1/Walmart_Sales.csv"
    assert detail_response.status_code == 200
    assert detail_response.json()["result"]["narrative"] == "Narrativa persistida"
    assert artifacts_response.status_code == 200
    assert {item["type"] for item in artifacts_response.json()} == {"response", "table"}


def test_failed_runs_are_listed_and_detail_preserves_persisted_error(repo_tmp_path: Path) -> None:
    artifacts_root = repo_tmp_path / "artifacts"
    store = FilesystemRunMetadataStore(artifacts_root=artifacts_root)

    def failing_agent_executor(request: RunRequest, context: AgentExecutionContext) -> AgentResult:
        raise RunError(
            code="llm_provider_unavailable",
            message="Ollama is unavailable for local generation",
            stage=ErrorStage.AGENT_EXECUTION,
            details={"provider": "ollama"},
        )

    client = TestClient(
        create_app(
            artifacts_root=artifacts_root,
            runtime_coordinator=build_runtime(
                artifacts_root=artifacts_root,
                store=store,
                agent_executor=failing_agent_executor,
            ),
            operational_readiness_service=StubReadinessService(artifacts_root),
            run_metadata_store=store,
        )
    )

    response = client.post(
        "/runs",
        json={
            "agent_id": "data_analyst",
            "dataset_path": "DatasetV1/Walmart_Sales.csv",
            "user_prompt": "Resume ventas",
        },
    )

    assert response.status_code == 503

    list_response = client.get("/runs")
    assert list_response.status_code == 200
    payload = list_response.json()
    assert len(payload) == 1
    assert payload[0]["status"] == "failed"

    run_id = payload[0]["run_id"]
    detail_response = client.get(f"/runs/{run_id}")

    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["status"] == "failed"
    assert detail_payload["error"]["code"] == "llm_provider_unavailable"
    assert detail_payload["error"]["stage"] == "agent_execution"
    assert detail_payload["result"] is None


def test_get_unknown_run_returns_404_api_error(repo_tmp_path: Path) -> None:
    artifacts_root = repo_tmp_path / "artifacts"
    store = FilesystemRunMetadataStore(artifacts_root=artifacts_root)
    client = TestClient(
        create_app(
            artifacts_root=artifacts_root,
            runtime_coordinator=build_runtime(
                artifacts_root=artifacts_root,
                store=store,
                agent_executor=lambda request, context: AgentResult(
                    narrative="unused",
                    findings=[],
                    sql_trace=[],
                    tables=[],
                    charts=[],
                    artifact_manifest=ArtifactManifest(run_id=context.run_id),
                ),
            ),
            operational_readiness_service=StubReadinessService(artifacts_root),
            run_metadata_store=store,
        )
    )

    response = client.get("/runs/run-missing")

    assert response.status_code == 404
    payload = response.json()
    assert payload["code"] == "run_not_found"
    assert payload["details"]["run_id"] == "run-missing"


def test_missing_artifact_files_keep_persisted_references_without_crashing(repo_tmp_path: Path) -> None:
    artifacts_root = repo_tmp_path / "artifacts"
    store = FilesystemRunMetadataStore(artifacts_root=artifacts_root)

    def fake_agent_executor(request: RunRequest, context: AgentExecutionContext) -> AgentResult:
        return AgentResult(
            narrative="Narrativa persistida",
            findings=["Hallazgo persistido"],
            sql_trace=[],
            tables=[TableResult(name="preview", rows=[{"sales": 10.5}])],
            charts=[],
            artifact_manifest=ArtifactManifest(run_id=context.run_id),
        )

    client = TestClient(
        create_app(
            artifacts_root=artifacts_root,
            runtime_coordinator=build_runtime(
                artifacts_root=artifacts_root,
                store=store,
                agent_executor=fake_agent_executor,
            ),
            operational_readiness_service=StubReadinessService(artifacts_root),
            run_metadata_store=store,
        )
    )

    post_response = client.post(
        "/runs",
        json={
            "agent_id": "data_analyst",
            "dataset_path": "DatasetV1/Walmart_Sales.csv",
            "user_prompt": "Resume ventas",
        },
    )
    run_id = post_response.json()["run_id"]

    first_artifacts_response = client.get(f"/runs/{run_id}/artifacts")
    for item in first_artifacts_response.json():
        Path(item["path"]).unlink()

    second_artifacts_response = client.get(f"/runs/{run_id}/artifacts")

    assert second_artifacts_response.status_code == 200
    payload = second_artifacts_response.json()
    assert {item["type"] for item in payload} == {"response", "table"}
    assert all(item["size_bytes"] is None for item in payload)


def test_provider_unavailable_error_maps_to_503(repo_tmp_path: Path) -> None:
    artifacts_root = repo_tmp_path / "artifacts"
    store = FilesystemRunMetadataStore(artifacts_root=artifacts_root)

    def failing_agent_executor(request: RunRequest, context: AgentExecutionContext) -> AgentResult:
        raise RunError(
            code="llm_provider_unavailable",
            message="Ollama is unavailable for local generation",
            stage=ErrorStage.AGENT_EXECUTION,
            details={"provider": "ollama"},
        )

    client = TestClient(
        create_app(
            artifacts_root=artifacts_root,
            runtime_coordinator=build_runtime(
                artifacts_root=artifacts_root,
                store=store,
                agent_executor=failing_agent_executor,
            ),
            operational_readiness_service=StubReadinessService(artifacts_root),
            run_metadata_store=store,
        )
    )

    response = client.post(
        "/runs",
        json={
            "agent_id": "data_analyst",
            "dataset_path": "DatasetV1/Walmart_Sales.csv",
            "user_prompt": "Resume ventas",
        },
    )

    assert response.status_code == 503
    payload = response.json()
    assert payload["code"] == "llm_provider_unavailable"
    assert payload["details"]["stage"] == "agent_execution"


def test_orphan_run_directories_without_metadata_are_ignored(repo_tmp_path: Path) -> None:
    artifacts_root = repo_tmp_path / "artifacts"
    store = FilesystemRunMetadataStore(artifacts_root=artifacts_root)
    orphan_dir = artifacts_root / "run-orphan"
    (orphan_dir / "tables").mkdir(parents=True, exist_ok=True)
    (orphan_dir / "response.md").write_text("orphan artifact\n", encoding="utf-8")

    client = TestClient(
        create_app(
            artifacts_root=artifacts_root,
            runtime_coordinator=build_runtime(
                artifacts_root=artifacts_root,
                store=store,
                agent_executor=lambda request, context: AgentResult(
                    narrative="unused",
                    findings=[],
                    sql_trace=[],
                    tables=[],
                    charts=[],
                    artifact_manifest=ArtifactManifest(run_id=context.run_id),
                ),
            ),
            operational_readiness_service=StubReadinessService(artifacts_root),
            run_metadata_store=store,
        )
    )

    response = client.get("/runs")

    assert response.status_code == 200
    assert response.json() == []
