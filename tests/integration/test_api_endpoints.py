import json
from io import StringIO
from pathlib import Path

from fastapi.testclient import TestClient
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
from artifacts import FilesystemRunMetadataStore, RUN_METADATA_FILENAME
from data import PreparedDataset
from interfaces.api import create_app
from observability import ApplicationHealth, ProveedorHealth, clear_context, configure_structured_logging
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


def configure_log_capture() -> StringIO:
    stream = StringIO()
    clear_context()
    configure_structured_logging(stream=stream, force=True)
    return stream


def parse_log_lines(stream: StringIO) -> list[dict[str, object]]:
    return [json.loads(line) for line in stream.getvalue().splitlines() if line.strip()]


def build_web_dist(root: Path) -> Path:
    web_dist = root / "web-dist"
    (web_dist / "assets").mkdir(parents=True, exist_ok=True)
    (web_dist / "index.html").write_text(
        "<!doctype html><html><body><div id='root'>packaged-ui</div></body></html>",
        encoding="utf-8",
    )
    (web_dist / "assets" / "app.js").write_text("console.log('packaged-ui');\n", encoding="utf-8")
    return web_dist


def test_post_runs_executes_core_and_persists_detail(repo_tmp_path: Path) -> None:
    artifacts_root = repo_tmp_path / "artifacts"
    store = FilesystemRunMetadataStore(artifacts_root=artifacts_root)
    log_stream = configure_log_capture()

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
    assert response.headers["X-Trace-Id"]
    payload = response.json()
    run_id = payload["run_id"]

    assert payload["agent_id"] == "data_analyst"
    assert payload["status"] == "succeeded"
    assert payload["dataset_profile"]["table_name"] == "dataset_run_api_001"
    assert payload["result"]["narrative"] == "Narrativa API"
    assert payload["artifact_manifest"]["run_id"] == run_id
    assert (artifacts_root / run_id / RUN_METADATA_FILENAME).is_file()

    log_payloads = parse_log_lines(log_stream)
    request_started = next(item for item in log_payloads if item["event"] == "request_started")
    run_started = next(item for item in log_payloads if item["event"] == "run_started")
    run_succeeded = next(item for item in log_payloads if item["event"] == "run_succeeded")
    assert request_started["trace_id"] == response.headers["X-Trace-Id"]
    assert run_started["trace_id"] == response.headers["X-Trace-Id"]
    assert run_started["run_id"] == run_id
    assert run_started["session_id"] == payload["session_id"]
    assert run_succeeded["trace_id"] == response.headers["X-Trace-Id"]
    assert run_succeeded["run_id"] == run_id


def test_chat_endpoints_create_persist_and_continue_session(repo_tmp_path: Path) -> None:
    artifacts_root = repo_tmp_path / "artifacts"
    store = FilesystemRunMetadataStore(artifacts_root=artifacts_root)
    captured_requests: list[RunRequest] = []

    def fake_agent_executor(request: RunRequest, context: AgentExecutionContext) -> AgentResult:
        captured_requests.append(request)
        return AgentResult(
            narrative=f"Respuesta para {request.user_prompt}",
            findings=["Hallazgo conversacional"],
            sql_trace=[],
            tables=[TableResult(name="ranking_Branch_by_Study_Hours_per_Day", rows=[{"Branch": "Civil", "avg": 4.26}])],
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

    create_response = client.post(
        "/chats",
        json={
            "agent_id": "data_analyst",
            "dataset_path": "DatasetV1/student_lifestyle_performance_dataset.csv",
            "user_prompt": "dime cual es la carrera en la que mas se estudia",
        },
    )

    assert create_response.status_code == 200
    chat = create_response.json()
    chat_id = chat["chat_id"]
    assert chat["dataset_path"] == "DatasetV1/student_lifestyle_performance_dataset.csv"
    assert chat["messages"][0]["role"] == "user"
    assert chat["messages"][1]["role"] == "assistant"
    assert chat["messages"][1]["result"]["narrative"].startswith("Respuesta para")
    assert chat["run_ids"] == [chat["messages"][1]["run_id"]]
    assert captured_requests[0].session_id == chat_id
    assert captured_requests[0].conversation_context == []

    follow_up_response = client.post(
        f"/chats/{chat_id}/messages",
        json={"user_prompt": "y comparalo con la segunda carrera"},
    )

    assert follow_up_response.status_code == 200
    continued = follow_up_response.json()
    assert continued["chat_id"] == chat_id
    assert len(continued["messages"]) == 4
    assert continued["messages"][-2]["content"] == "y comparalo con la segunda carrera"
    assert continued["messages"][-1]["role"] == "assistant"
    assert len(continued["run_ids"]) == 2
    assert captured_requests[1].session_id == chat_id
    assert captured_requests[1].conversation_context[-2:] == [
        {"role": "user", "content": "dime cual es la carrera en la que mas se estudia"},
        {"role": "assistant", "content": "Respuesta para dime cual es la carrera en la que mas se estudia"},
    ]

    list_response = client.get("/chats")
    assert list_response.status_code == 200
    assert list_response.json()[0]["chat_id"] == chat_id

    restarted_client = TestClient(
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
    persisted_response = restarted_client.get(f"/chats/{chat_id}")
    assert persisted_response.status_code == 200
    assert len(persisted_response.json()["messages"]) == 4


def test_chat_endpoint_persists_failed_agent_message(repo_tmp_path: Path) -> None:
    artifacts_root = repo_tmp_path / "artifacts"
    store = FilesystemRunMetadataStore(artifacts_root=artifacts_root)

    def failing_agent_executor(request: RunRequest, context: AgentExecutionContext) -> AgentResult:
        raise RunError(
            code="llm_provider_unavailable",
            message="Ollama is unavailable for local generation",
            stage=ErrorStage.AGENT_EXECUTION,
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
        "/chats",
        json={
            "agent_id": "data_analyst",
            "dataset_path": "DatasetV1/Walmart_Sales.csv",
            "user_prompt": "Resume ventas",
        },
    )

    assert response.status_code == 503
    chat = client.get("/chats").json()[0]
    detail = client.get(f"/chats/{chat['chat_id']}").json()
    assert detail["messages"][-1]["role"] == "assistant"
    assert detail["messages"][-1]["status"] == "failed"
    assert detail["messages"][-1]["error"]["code"] == "llm_provider_unavailable"


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
    assert response.headers["X-Trace-Id"]
    payload = response.json()
    assert payload["code"] == "invalid_request"
    assert payload["status"] == 400
    assert payload["details"]["stage"] == "request_validation"
    assert payload["details"]["category"] == "request"
    assert payload["trace_id"]
    assert payload["trace_id"] == response.headers["X-Trace-Id"]


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
    assert response.headers["X-Trace-Id"]
    assert response.json()["status"] == "ok"
    assert response.json()["artifacts_root"] == str(artifacts_root)
    assert provider_response.status_code == 200
    assert provider_response.headers["X-Trace-Id"]
    assert provider_response.json()["proveedor"] == "ollama"
    assert provider_response.json()["model_available"] is True


def test_get_local_datasets_lists_supported_datasetv1_files(repo_tmp_path: Path) -> None:
    artifacts_root = repo_tmp_path / "artifacts"
    dataset_root = repo_tmp_path / "DatasetV1"
    dataset_root.mkdir()
    csv_path = dataset_root / "student_lifestyle_performance_dataset.csv"
    xlsx_path = dataset_root / "Walmart_Sales.xlsx"
    ignored_path = dataset_root / "notes.txt"
    csv_path.write_text("a,b\n1,2\n", encoding="utf-8")
    xlsx_path.write_bytes(b"fake-xlsx-for-listing-only")
    ignored_path.write_text("not a dataset\n", encoding="utf-8")
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
            local_datasets_root=dataset_root,
        )
    )

    response = client.get("/datasets/local")

    assert response.status_code == 200
    assert response.headers["X-Trace-Id"]
    assert response.json() == [
        {
            "name": "Walmart_Sales.xlsx",
            "label": "Walmart Sales",
            "path": str(Path("DatasetV1") / "Walmart_Sales.xlsx").replace("\\", "/"),
            "format": "xlsx",
            "size_bytes": xlsx_path.stat().st_size,
        },
        {
            "name": "student_lifestyle_performance_dataset.csv",
            "label": "Student lifestyle performance dataset",
            "path": str(Path("DatasetV1") / "student_lifestyle_performance_dataset.csv").replace("\\", "/"),
            "format": "csv",
            "size_bytes": csv_path.stat().st_size,
        },
    ]


def test_get_local_datasets_returns_empty_list_when_datasetv1_missing(repo_tmp_path: Path) -> None:
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
            local_datasets_root=repo_tmp_path / "missing-DatasetV1",
        )
    )

    response = client.get("/datasets/local")

    assert response.status_code == 200
    assert response.json() == []


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
    assert response.headers["X-Trace-Id"]

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
    assert detail_payload["error"]["details"]["category"] == "provider"
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
    assert response.headers["X-Trace-Id"]
    payload = response.json()
    assert payload["code"] == "run_not_found"
    assert payload["details"]["category"] == "request"
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
    assert response.headers["X-Trace-Id"]
    payload = response.json()
    assert payload["code"] == "llm_provider_unavailable"
    assert payload["details"]["category"] == "provider"
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


def test_packaged_web_root_is_served_without_hiding_api_endpoints(repo_tmp_path: Path) -> None:
    artifacts_root = repo_tmp_path / "artifacts"
    store = FilesystemRunMetadataStore(artifacts_root=artifacts_root)
    web_dist = build_web_dist(repo_tmp_path)
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
            serve_web=True,
            web_dist=web_dist,
        )
    )

    root_response = client.get("/")
    asset_response = client.get("/assets/app.js")
    health_response = client.get("/health")

    assert root_response.status_code == 200
    assert "text/html" in root_response.headers["content-type"]
    assert "packaged-ui" in root_response.text
    assert asset_response.status_code == 200
    assert "packaged-ui" in asset_response.text
    assert health_response.status_code == 200
    assert health_response.json()["status"] == "ok"


def test_packaged_web_requires_existing_build(repo_tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Run 'npm --prefix interfaces/web run build' before using --serve-web"):
        create_app(
            artifacts_root=repo_tmp_path / "artifacts",
            runtime_coordinator=build_runtime(
                artifacts_root=repo_tmp_path / "artifacts",
                store=FilesystemRunMetadataStore(artifacts_root=repo_tmp_path / "artifacts"),
                agent_executor=lambda request, context: AgentResult(
                    narrative="unused",
                    findings=[],
                    sql_trace=[],
                    tables=[],
                    charts=[],
                    artifact_manifest=ArtifactManifest(run_id=context.run_id),
                ),
            ),
            operational_readiness_service=StubReadinessService(repo_tmp_path / "artifacts"),
            run_metadata_store=FilesystemRunMetadataStore(artifacts_root=repo_tmp_path / "artifacts"),
            serve_web=True,
            web_dist=repo_tmp_path / "missing-web-dist",
        )
