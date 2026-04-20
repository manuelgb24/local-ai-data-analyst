"""Application layer public exports for the MVP."""

from .api_contracts import (
    ArtifactListItem,
    ChatDetail,
    ChatMessage,
    ChatNotFoundError,
    ChatSummary,
    RunDetail,
    RunNotFoundError,
    RunSummary,
)
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
    if name == "GetRunUseCase":
        from .run_history import GetRunUseCase

        return GetRunUseCase
    if name == "ListRunArtifactsUseCase":
        from .run_history import ListRunArtifactsUseCase

        return ListRunArtifactsUseCase
    if name == "ListRunsUseCase":
        from .run_history import ListRunsUseCase

        return ListRunsUseCase
    if name == "CreateChatUseCase":
        from .chat_history import CreateChatUseCase

        return CreateChatUseCase
    if name == "GetChatUseCase":
        from .chat_history import GetChatUseCase

        return GetChatUseCase
    if name == "ListChatsUseCase":
        from .chat_history import ListChatsUseCase

        return ListChatsUseCase
    if name == "SendChatMessageUseCase":
        from .chat_history import SendChatMessageUseCase

        return SendChatMessageUseCase
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "AgentExecutionContext",
    "AgentResult",
    "ArtifactListItem",
    "ArtifactManifest",
    "ChatDetail",
    "ChatMessage",
    "ChatNotFoundError",
    "ChatSummary",
    "ChartReference",
    "CreateChatUseCase",
    "DatasetColumn",
    "DatasetProfile",
    "ErrorStage",
    "GetAppConfigUseCase",
    "GetOperationalStatusUseCase",
    "GetRunUseCase",
    "GetChatUseCase",
    "ListChatsUseCase",
    "ListRunArtifactsUseCase",
    "ListRunsUseCase",
    "RunDetail",
    "RunError",
    "RunNotFoundError",
    "RunRequest",
    "RunSummary",
    "RunState",
    "SqlTraceEntry",
    "SqlTraceStatus",
    "TableResult",
    "RunAnalysisUseCase",
    "SendChatMessageUseCase",
]
