"""Application use cases for operational status and config inspection."""

from __future__ import annotations

from observability import AppConfig, OperationalReadinessService, ReadinessReport


class GetAppConfigUseCase:
    """Expose effective local configuration without leaking CLI concerns."""

    def __init__(self, readiness_service: OperationalReadinessService) -> None:
        self._readiness_service = readiness_service

    def execute(self) -> AppConfig:
        return self._readiness_service.get_app_config()


class GetOperationalStatusUseCase:
    """Expose readiness and health checks as an application-level query."""

    def __init__(self, readiness_service: OperationalReadinessService) -> None:
        self._readiness_service = readiness_service

    def execute(self) -> ReadinessReport:
        return self._readiness_service.get_readiness_report()

