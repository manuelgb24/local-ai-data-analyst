"""Structured contracts for local readiness, provider health, and app config."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


def _require_non_empty_string(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty string")

    return normalized


def _require_bool(value: bool, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{field_name} must be a boolean")
    return value


class HealthStatus(Enum):
    OK = "ok"
    ERROR = "error"


@dataclass(slots=True)
class AppConfig:
    default_agent_id: str
    supported_dataset_formats: list[str]
    proveedor_name: str
    proveedor_endpoint: str
    required_model: str

    def __post_init__(self) -> None:
        self.default_agent_id = _require_non_empty_string(self.default_agent_id, "default_agent_id")
        self.supported_dataset_formats = sorted(
            {_require_non_empty_string(item, "supported_dataset_formats[]").lower() for item in self.supported_dataset_formats}
        )
        if not self.supported_dataset_formats:
            raise ValueError("supported_dataset_formats must contain at least one format")
        self.proveedor_name = _require_non_empty_string(self.proveedor_name, "proveedor_name")
        self.proveedor_endpoint = _require_non_empty_string(self.proveedor_endpoint, "proveedor_endpoint")
        self.required_model = _require_non_empty_string(self.required_model, "required_model")


@dataclass(slots=True)
class ApplicationHealth:
    ready: bool
    default_agent_id: str
    artifacts_root: str
    checks: dict[str, bool] = field(default_factory=dict)
    details: list[str] = field(default_factory=list)
    status: HealthStatus = field(init=False)

    def __post_init__(self) -> None:
        self.ready = _require_bool(self.ready, "ready")
        self.default_agent_id = _require_non_empty_string(self.default_agent_id, "default_agent_id")
        self.artifacts_root = _require_non_empty_string(self.artifacts_root, "artifacts_root")
        self.checks = {str(key): _require_bool(value, f"checks[{key}]") for key, value in dict(self.checks).items()}
        self.details = [_require_non_empty_string(item, "details[]") for item in self.details]
        self.status = HealthStatus.OK if self.ready else HealthStatus.ERROR


@dataclass(slots=True)
class ProveedorHealth:
    proveedor: str
    endpoint: str
    reachable: bool
    model: str
    model_available: bool
    binary_available: bool
    binary_path: str | None = None
    version: str | None = None
    details: list[str] = field(default_factory=list)
    ready: bool = field(init=False)
    status: HealthStatus = field(init=False)

    def __post_init__(self) -> None:
        self.proveedor = _require_non_empty_string(self.proveedor, "proveedor")
        self.endpoint = _require_non_empty_string(self.endpoint, "endpoint")
        self.reachable = _require_bool(self.reachable, "reachable")
        self.model = _require_non_empty_string(self.model, "model")
        self.model_available = _require_bool(self.model_available, "model_available")
        self.binary_available = _require_bool(self.binary_available, "binary_available")
        if self.binary_path is not None:
            self.binary_path = _require_non_empty_string(self.binary_path, "binary_path")
        if self.version is not None:
            self.version = _require_non_empty_string(self.version, "version")
        self.details = [_require_non_empty_string(item, "details[]") for item in self.details]
        self.ready = self.binary_available and self.reachable and self.model_available
        self.status = HealthStatus.OK if self.ready else HealthStatus.ERROR


@dataclass(slots=True)
class ReadinessReport:
    application: ApplicationHealth
    provider: ProveedorHealth
    issues: list[str] = field(default_factory=list)
    ready: bool = field(init=False)
    status: HealthStatus = field(init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.application, ApplicationHealth):
            raise TypeError("application must be an ApplicationHealth instance")
        if not isinstance(self.provider, ProveedorHealth):
            raise TypeError("provider must be a ProveedorHealth instance")
        self.issues = [_require_non_empty_string(item, "issues[]") for item in self.issues]
        self.ready = self.application.ready and self.provider.ready
        self.status = HealthStatus.OK if self.ready else HealthStatus.ERROR

