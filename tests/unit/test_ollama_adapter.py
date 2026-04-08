import json
import socket
import subprocess
import sys
import textwrap
from urllib.error import HTTPError, URLError

import pytest

from adapters import DEFAULT_OLLAMA_BASE_URL, DEFAULT_OLLAMA_TIMEOUT_SECONDS, OllamaLLMAdapter
from agents.data_analyst import DATA_ANALYST_AGENT_CONFIG, build_data_analyst_llm_adapter
from application import ErrorStage, RunError


class FakeHTTPResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "FakeHTTPResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_ollama_adapter_generate_returns_model_response(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = OllamaLLMAdapter(model="deepseek-r1:8b", base_url="http://ollama.local", timeout_seconds=5)
    observed: dict[str, object] = {}

    def fake_urlopen(request, timeout: float):
        observed["url"] = request.full_url
        observed["timeout"] = timeout
        observed["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeHTTPResponse(b'{"response": "  Analisis listo  "}')

    monkeypatch.setattr("adapters.ollama_adapter.urlopen", fake_urlopen)

    result = adapter.generate("Resume el dataset")

    assert result == "Analisis listo"
    assert observed == {
        "url": "http://ollama.local/api/generate",
        "timeout": 5.0,
        "payload": {
            "model": "deepseek-r1:8b",
            "prompt": "Resume el dataset",
            "stream": False,
        },
    }


def test_data_analyst_llm_adapter_uses_fixed_mvp_model(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: dict[str, object] = {}

    def fake_urlopen(request, timeout: float):
        observed["timeout"] = timeout
        observed["url"] = request.full_url
        observed["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeHTTPResponse(b'{"response": "OK"}')

    monkeypatch.setattr("adapters.ollama_adapter.urlopen", fake_urlopen)

    adapter = build_data_analyst_llm_adapter()
    result = adapter.generate("Di OK")

    assert result == "OK"
    assert observed == {
        "timeout": DEFAULT_OLLAMA_TIMEOUT_SECONDS,
        "url": f"{DEFAULT_OLLAMA_BASE_URL}/api/generate",
        "payload": {
            "model": DATA_ANALYST_AGENT_CONFIG["model"],
            "prompt": "Di OK",
            "stream": False,
        },
    }


@pytest.mark.parametrize("invalid_timeout", ["10", True, 0, -1, 0.0])
def test_ollama_adapter_rejects_invalid_timeout_values(invalid_timeout: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        OllamaLLMAdapter(model="deepseek-r1:8b", timeout_seconds=invalid_timeout)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("raised_exception", "expected_reason"),
    [
        pytest.param(URLError("connection refused"), "connection refused", id="url-error"),
        pytest.param(socket.timeout("timed out"), "timed out", id="socket-timeout"),
    ],
)
def test_ollama_adapter_maps_provider_unavailable_errors(
    monkeypatch: pytest.MonkeyPatch,
    raised_exception: Exception,
    expected_reason: str,
) -> None:
    adapter = OllamaLLMAdapter(model="deepseek-r1:8b")

    def fake_urlopen(request, timeout: float):
        raise raised_exception

    monkeypatch.setattr("adapters.ollama_adapter.urlopen", fake_urlopen)

    with pytest.raises(RunError) as exc_info:
        adapter.generate("Resume el dataset")

    assert exc_info.value.code == "llm_provider_unavailable"
    assert exc_info.value.stage is ErrorStage.AGENT_EXECUTION
    assert exc_info.value.details is not None
    assert exc_info.value.details["base_url"] == DEFAULT_OLLAMA_BASE_URL
    assert expected_reason in exc_info.value.details["reason"]
    assert "auto_start_attempted" not in exc_info.value.details


def test_ollama_adapter_maps_http_errors_to_generation_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = OllamaLLMAdapter(model="deepseek-r1:8b")

    def fake_urlopen(request, timeout: float):
        raise HTTPError(
            url=request.full_url,
            code=503,
            msg="Service Unavailable",
            hdrs=None,
            fp=None,
        )

    monkeypatch.setattr("adapters.ollama_adapter.urlopen", fake_urlopen)

    with pytest.raises(RunError) as exc_info:
        adapter.generate("Resume el dataset")

    assert exc_info.value.code == "llm_generation_failed"
    assert exc_info.value.stage is ErrorStage.AGENT_EXECUTION
    assert exc_info.value.details == {
        "http_status": 503,
        "provider": "ollama",
        "model": "deepseek-r1:8b",
        "reason": "Service Unavailable",
    }


@pytest.mark.parametrize(
    ("payload", "expected_message"),
    [
        pytest.param(b"not-json", "Ollama returned an invalid JSON payload", id="invalid-json"),
        pytest.param(b'{"response": ""}', "Ollama returned an empty response", id="empty-response"),
        pytest.param(b'{"error": "model not found"}', "Ollama reported a generation error", id="provider-error"),
    ],
)
def test_ollama_adapter_rejects_invalid_provider_payloads(
    monkeypatch: pytest.MonkeyPatch,
    payload: bytes,
    expected_message: str,
) -> None:
    adapter = OllamaLLMAdapter(model="deepseek-r1:8b")

    def fake_urlopen(request, timeout: float):
        return FakeHTTPResponse(payload)

    monkeypatch.setattr("adapters.ollama_adapter.urlopen", fake_urlopen)

    with pytest.raises(RunError) as exc_info:
        adapter.generate("Resume el dataset")

    assert exc_info.value.code == "llm_generation_failed"
    assert exc_info.value.message == expected_message
    assert exc_info.value.stage is ErrorStage.AGENT_EXECUTION


@pytest.mark.parametrize(
    "import_order",
    [
        (
            "from adapters import OllamaLLMAdapter\n"
            "from agents.data_analyst import build_data_analyst_llm_adapter\n"
            "from application import RunAnalysisUseCase\n"
        ),
        (
            "from application import RunAnalysisUseCase\n"
            "from agents.data_analyst import build_data_analyst_llm_adapter\n"
            "from adapters import OllamaLLMAdapter\n"
        ),
        (
            "from agents.data_analyst import build_data_analyst_llm_adapter\n"
            "from adapters import OllamaLLMAdapter\n"
            "from application import RunAnalysisUseCase\n"
        ),
    ],
)
def test_public_import_orders_do_not_trigger_cycles(import_order: str) -> None:
    script = textwrap.dedent(
        import_order
        + "\n"
        + "print(OllamaLLMAdapter.__name__)\n"
        + "print(build_data_analyst_llm_adapter.__name__)\n"
        + "print(RunAnalysisUseCase.__name__)\n"
    )

    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "OllamaLLMAdapter" in completed.stdout
    assert "build_data_analyst_llm_adapter" in completed.stdout
    assert "RunAnalysisUseCase" in completed.stdout
