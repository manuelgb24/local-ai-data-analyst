"""Minimal Ollama adapter for the MVP fixed local LLM integration."""

from __future__ import annotations

from dataclasses import dataclass
import json
import shutil
import socket
import subprocess
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from application.contracts import ErrorStage, RunError


DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_TIMEOUT_SECONDS = 120.0
DEFAULT_OLLAMA_COMMAND_TIMEOUT_SECONDS = 20.0


def _require_non_empty_string(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty string")

    return normalized


def _require_positive_timeout_seconds(value: float, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a positive number")

    normalized = float(value)
    if normalized <= 0:
        raise ValueError(f"{field_name} must be greater than 0")

    return normalized


@dataclass(slots=True)
class OllamaBinaryProbeResult:
    available: bool
    path: str | None = None
    detail: str | None = None


@dataclass(slots=True)
class OllamaEndpointProbeResult:
    reachable: bool
    version: str | None = None
    detail: str | None = None


@dataclass(slots=True)
class OllamaModelProbeResult:
    available: bool
    detail: str | None = None


def probe_ollama_binary() -> OllamaBinaryProbeResult:
    binary_path = shutil.which("ollama")
    if binary_path is None:
        return OllamaBinaryProbeResult(
            available=False,
            detail="El binario `ollama` no está disponible en PATH.",
        )
    return OllamaBinaryProbeResult(available=True, path=binary_path)


def probe_ollama_endpoint(
    base_url: str = DEFAULT_OLLAMA_BASE_URL,
    timeout_seconds: float = 5.0,
) -> OllamaEndpointProbeResult:
    normalized_base_url = _require_non_empty_string(base_url, "base_url").rstrip("/")
    normalized_timeout = _require_positive_timeout_seconds(timeout_seconds, "timeout_seconds")

    try:
        with urlopen(f"{normalized_base_url}/api/version", timeout=normalized_timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
        return OllamaEndpointProbeResult(
            reachable=False,
            detail=(
                f"Ollama no responde correctamente en {normalized_base_url}. "
                f"Detalle: {type(exc).__name__}: {exc}"
            ),
        )

    version = payload.get("version")
    if not isinstance(version, str) or not version.strip():
        return OllamaEndpointProbeResult(
            reachable=False,
            detail=(
                f"Ollama respondió en {normalized_base_url} pero devolvió una versión inválida. "
                f"Payload: {payload}"
            ),
        )

    return OllamaEndpointProbeResult(reachable=True, version=version.strip())


def probe_ollama_model(
    model_name: str,
    timeout_seconds: float = DEFAULT_OLLAMA_COMMAND_TIMEOUT_SECONDS,
) -> OllamaModelProbeResult:
    normalized_model_name = _require_non_empty_string(model_name, "model_name")
    normalized_timeout = _require_positive_timeout_seconds(timeout_seconds, "timeout_seconds")

    binary_probe = probe_ollama_binary()
    if not binary_probe.available:
        return OllamaModelProbeResult(
            available=False,
            detail=binary_probe.detail or "No se pudo ejecutar `ollama list` porque el binario no está disponible.",
        )

    try:
        completed = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=normalized_timeout,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return OllamaModelProbeResult(
            available=False,
            detail=f"No se pudo ejecutar `ollama list`. Detalle: {type(exc).__name__}: {exc}",
        )

    if completed.returncode != 0:
        return OllamaModelProbeResult(
            available=False,
            detail=(
                "No se pudo comprobar la lista de modelos de Ollama. "
                f"Exit code: {completed.returncode}. Stderr: {completed.stderr.strip()}"
            ),
        )

    if normalized_model_name not in completed.stdout:
        return OllamaModelProbeResult(
            available=False,
            detail=f"El modelo requerido no aparece instalado en Ollama: {normalized_model_name}.",
        )

    return OllamaModelProbeResult(available=True)


class OllamaLLMAdapter:
    """Thin adapter over Ollama's local HTTP API for the MVP."""

    def __init__(
        self,
        model: str,
        base_url: str = DEFAULT_OLLAMA_BASE_URL,
        timeout_seconds: float = DEFAULT_OLLAMA_TIMEOUT_SECONDS,
    ) -> None:
        self._model = _require_non_empty_string(model, "model")
        self._base_url = _require_non_empty_string(base_url, "base_url").rstrip("/")
        self._timeout_seconds = _require_positive_timeout_seconds(timeout_seconds, "timeout_seconds")

    def generate(self, prompt: str) -> str:
        prompt = _require_non_empty_string(prompt, "prompt")
        payload = json.dumps(
            {
                "model": self._model,
                "prompt": prompt,
                "stream": False,
            }
        ).encode("utf-8")
        request = Request(
            url=f"{self._base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                response_body = response.read()
        except HTTPError as exc:
            raise self._build_generation_error(
                message="Ollama returned a non-success status",
                details={
                    "http_status": exc.code,
                    "provider": "ollama",
                    "model": self._model,
                    "reason": exc.reason,
                },
            ) from exc
        except (URLError, TimeoutError, socket.timeout, OSError) as exc:
            raise self._build_provider_unavailable_error(
                "Ollama is unavailable for local generation",
                {
                    "provider": "ollama",
                    "model": self._model,
                    "base_url": self._base_url,
                    "error_type": type(exc).__name__,
                    "reason": str(getattr(exc, "reason", exc)),
                },
            ) from exc

        return self._parse_response_body(response_body)

    def _parse_response_body(self, response_body: bytes) -> str:
        try:
            payload = json.loads(response_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise self._build_generation_error(
                message="Ollama returned an invalid JSON payload",
                details={
                    "provider": "ollama",
                    "model": self._model,
                    "response_preview": response_body[:200].decode("utf-8", errors="replace"),
                },
            ) from exc

        if not isinstance(payload, dict):
            raise self._build_generation_error(
                message="Ollama returned an unexpected response payload",
                details={
                    "provider": "ollama",
                    "model": self._model,
                    "payload_type": type(payload).__name__,
                },
            )

        provider_error = payload.get("error")
        if isinstance(provider_error, str) and provider_error.strip():
            raise self._build_generation_error(
                message="Ollama reported a generation error",
                details={
                    "provider": "ollama",
                    "model": self._model,
                    "provider_error": provider_error.strip(),
                },
            )

        response_text = payload.get("response")
        if not isinstance(response_text, str) or not response_text.strip():
            raise self._build_generation_error(
                message="Ollama returned an empty response",
                details={
                    "provider": "ollama",
                    "model": self._model,
                },
            )

        return response_text.strip()

    def _build_provider_unavailable_error(self, message: str, details: dict[str, Any]) -> RunError:
        return RunError(
            code="llm_provider_unavailable",
            message=message,
            stage=ErrorStage.AGENT_EXECUTION,
            details=details,
        )

    def _build_generation_error(self, message: str, details: dict[str, Any]) -> RunError:
        return RunError(
            code="llm_generation_failed",
            message=message,
            stage=ErrorStage.AGENT_EXECUTION,
            details=details,
        )


__all__ = [
    "DEFAULT_OLLAMA_COMMAND_TIMEOUT_SECONDS",
    "DEFAULT_OLLAMA_BASE_URL",
    "DEFAULT_OLLAMA_TIMEOUT_SECONDS",
    "OllamaBinaryProbeResult",
    "OllamaEndpointProbeResult",
    "OllamaLLMAdapter",
    "OllamaModelProbeResult",
    "probe_ollama_binary",
    "probe_ollama_endpoint",
    "probe_ollama_model",
]
