"""Main application use case for running the MVP flow."""

from __future__ import annotations

from application.contracts import AgentResult, RunRequest
from runtime import RuntimeCoordinator


class RunAnalysisUseCase:
    """Thin application-layer adapter over the runtime coordinator."""

    def __init__(self, runtime: RuntimeCoordinator) -> None:
        self._runtime = runtime

    def execute(self, request: RunRequest) -> AgentResult:
        if not isinstance(request, RunRequest):
            raise TypeError("request must be a RunRequest instance")
        return self._runtime.run(request)
