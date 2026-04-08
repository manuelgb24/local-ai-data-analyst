"""Service layer for local operational readiness and config inspection."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path
from uuid import uuid4

from adapters import (
    DEFAULT_OLLAMA_BASE_URL,
    OllamaBinaryProbeResult,
    OllamaEndpointProbeResult,
    OllamaModelProbeResult,
    probe_ollama_binary,
    probe_ollama_endpoint,
    probe_ollama_model,
)
from agents.data_analyst import DATA_ANALYST_AGENT_CONFIG, DATA_ANALYST_AGENT_ID
from application.contracts import RunRequest
from runtime import AgentRegistry, build_default_agent_registry

from .models import AppConfig, ApplicationHealth, ProveedorHealth, ReadinessReport

BinaryProbe = Callable[[], OllamaBinaryProbeResult]
EndpointProbe = Callable[[str, float], OllamaEndpointProbeResult]
ModelProbe = Callable[[str, float], OllamaModelProbeResult]

DEFAULT_PROVIDER_NAME = "ollama"
DEFAULT_PROVIDER_TIMEOUT_SECONDS = 5.0


class OperationalReadinessService:
    """Compose local app wiring and provider checks for operational status."""

    def __init__(
        self,
        *,
        agent_registry: AgentRegistry,
        artifacts_root: str | Path = "artifacts/runs",
        default_agent_id: str = DATA_ANALYST_AGENT_ID,
        provider_name: str = DEFAULT_PROVIDER_NAME,
        provider_endpoint: str = DEFAULT_OLLAMA_BASE_URL,
        required_model: str = DATA_ANALYST_AGENT_CONFIG["model"],
        supported_dataset_formats: Iterable[str] = RunRequest.SUPPORTED_FORMATS,
        provider_timeout_seconds: float = DEFAULT_PROVIDER_TIMEOUT_SECONDS,
        binary_probe: BinaryProbe = probe_ollama_binary,
        endpoint_probe: EndpointProbe = probe_ollama_endpoint,
        model_probe: ModelProbe = probe_ollama_model,
    ) -> None:
        self._agent_registry = agent_registry
        self._artifacts_root = Path(artifacts_root)
        self._default_agent_id = str(default_agent_id)
        self._provider_name = str(provider_name)
        self._provider_endpoint = str(provider_endpoint)
        self._required_model = str(required_model)
        self._supported_dataset_formats = list(supported_dataset_formats)
        self._provider_timeout_seconds = float(provider_timeout_seconds)
        self._binary_probe = binary_probe
        self._endpoint_probe = endpoint_probe
        self._model_probe = model_probe

    def get_app_config(self) -> AppConfig:
        return AppConfig(
            default_agent_id=self._default_agent_id,
            supported_dataset_formats=self._supported_dataset_formats,
            proveedor_name=self._provider_name,
            proveedor_endpoint=self._provider_endpoint,
            required_model=self._required_model,
        )

    def get_application_health(self) -> ApplicationHealth:
        config = self.get_app_config()
        details: list[str] = []

        agent_ready = self._is_agent_registered(details)
        artifacts_ready = self._is_artifacts_root_writable(details)
        checks = {
            "agent_registry": agent_ready,
            "artifacts_root_writable": artifacts_ready,
            "config_available": True,
        }

        return ApplicationHealth(
            ready=all(checks.values()),
            default_agent_id=config.default_agent_id,
            artifacts_root=str(self._artifacts_root),
            checks=checks,
            details=details,
        )

    def get_provider_health(self) -> ProveedorHealth:
        config = self.get_app_config()
        details: list[str] = []

        binary_result = self._binary_probe()
        endpoint_result = self._endpoint_probe(config.proveedor_endpoint, self._provider_timeout_seconds)

        if binary_result.available:
            model_result = self._model_probe(config.required_model, self._provider_timeout_seconds)
        else:
            model_result = OllamaModelProbeResult(
                available=False,
                detail="No se pudo comprobar el modelo porque `ollama` no está disponible en PATH.",
            )

        if not binary_result.available:
            details.append(
                binary_result.detail
                or "El binario `ollama` no está disponible en PATH. Instala Ollama antes de usar el producto."
            )
        if not endpoint_result.reachable:
            details.append(
                endpoint_result.detail
                or (
                    f"Ollama no responde en {config.proveedor_endpoint}. "
                    "Levanta `ollama serve`, confirma el puerto local y reintenta."
                )
            )
        if binary_result.available and not model_result.available:
            details.append(
                model_result.detail
                or (
                    f"El modelo requerido no está disponible en Ollama: {config.required_model}. "
                    "Ejecuta `ollama pull` para instalarlo localmente."
                )
            )

        return ProveedorHealth(
            proveedor=config.proveedor_name,
            endpoint=config.proveedor_endpoint,
            reachable=endpoint_result.reachable,
            model=config.required_model,
            model_available=model_result.available,
            binary_available=binary_result.available,
            binary_path=binary_result.path,
            version=endpoint_result.version,
            details=details,
        )

    def get_readiness_report(self) -> ReadinessReport:
        application = self.get_application_health()
        provider = self.get_provider_health()
        return ReadinessReport(
            application=application,
            provider=provider,
            issues=[*application.details, *provider.details],
        )

    def _is_agent_registered(self, details: list[str]) -> bool:
        try:
            self._agent_registry.resolve(self._default_agent_id)
        except Exception as exc:
            details.append(
                f"El agente por defecto configurado no es resoluble: {self._default_agent_id}. "
                f"Detalle: {type(exc).__name__}: {exc}"
            )
            return False
        return True

    def _is_artifacts_root_writable(self, details: list[str]) -> bool:
        try:
            self._artifacts_root.mkdir(parents=True, exist_ok=True)
            probe_path = self._artifacts_root / f".write-probe-{uuid4().hex}"
            probe_path.write_text("ok", encoding="utf-8")
            probe_path.unlink()
        except OSError as exc:
            details.append(
                f"No se puede usar el directorio de artifacts configurado ({self._artifacts_root}). "
                f"Detalle: {type(exc).__name__}: {exc}"
            )
            return False
        return True


def build_default_operational_readiness_service(
    artifacts_root: str | Path = "artifacts/runs",
) -> OperationalReadinessService:
    """Build the default readiness service wired for the current local product."""

    return OperationalReadinessService(
        agent_registry=build_default_agent_registry(),
        artifacts_root=artifacts_root,
    )

