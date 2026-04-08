from __future__ import annotations

import pytest

from agents.data_analyst import DATA_ANALYST_AGENT_CONFIG
from observability import OperationalReadinessService
from runtime import build_default_agent_registry


def _build_service(
    *,
    base_url: str = "http://127.0.0.1:11434",
    model_name: str = DATA_ANALYST_AGENT_CONFIG["model"],
    timeout_seconds: float = 5.0,
) -> OperationalReadinessService:
    return OperationalReadinessService(
        agent_registry=build_default_agent_registry(),
        artifacts_root="artifacts/runs",
        provider_endpoint=base_url,
        required_model=model_name,
        provider_timeout_seconds=timeout_seconds,
    )


def require_ollama_binary() -> None:
    provider = _build_service().get_provider_health()
    if not provider.binary_available:
        pytest.skip(
            "El binario `ollama` no está disponible en PATH. "
            "Instala Ollama o inicia el servicio manualmente antes de ejecutar este smoke."
        )


def require_ready_ollama(base_url: str = "http://127.0.0.1:11434", timeout_seconds: float = 5.0) -> None:
    provider = _build_service(base_url=base_url, timeout_seconds=timeout_seconds).get_provider_health()
    if not provider.reachable:
        pytest.skip(
            "Ollama no está listo para los smokes reales en este entorno. "
            "Levanta/estabiliza `ollama serve`, confirma el puerto 11434 y reintenta. "
            f"Detalle: {provider.details}"
        )


def require_installed_model(model_name: str = DATA_ANALYST_AGENT_CONFIG["model"]) -> None:
    provider = _build_service(model_name=model_name).get_provider_health()
    if not provider.model_available:
        pytest.skip(
            f"El modelo requerido para el MVP no aparece instalado en Ollama: {model_name}. "
            f"Detalle: {provider.details}"
        )
