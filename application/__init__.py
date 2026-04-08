"""Application layer public exports for the MVP."""

from .contracts import (
    AgentExecutionContext,
    AgentResult,
    ArtifactManifest,
    ChartReference,
    DatasetColumn,
    DatasetProfile,
    ErrorStage,
    RunError,
    RunRequest,
    RunState,
    SqlTraceEntry,
    SqlTraceStatus,
    TableResult,
)


def __getattr__(name: str):
    if name == "RunAnalysisUseCase":
        from .run_analysis import RunAnalysisUseCase

        return RunAnalysisUseCase
    if name == "GetAppConfigUseCase":
        from .operations import GetAppConfigUseCase

        return GetAppConfigUseCase
    if name == "GetOperationalStatusUseCase":
        from .operations import GetOperationalStatusUseCase

        return GetOperationalStatusUseCase
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "AgentExecutionContext",
    "AgentResult",
    "ArtifactManifest",
    "ChartReference",
    "DatasetColumn",
    "DatasetProfile",
    "ErrorStage",
    "GetAppConfigUseCase",
    "GetOperationalStatusUseCase",
    "RunError",
    "RunRequest",
    "RunState",
    "SqlTraceEntry",
    "SqlTraceStatus",
    "TableResult",
    "RunAnalysisUseCase",
]
