"""Read-side contracts for the local API and persisted run history."""

from __future__ import annotations

from dataclasses import dataclass, field

from .contracts import AgentResult, ArtifactManifest, DatasetProfile, RunError, RunState


def _require_non_empty_string(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty string")

    return normalized


def _normalize_optional_string(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_non_empty_string(value, field_name)


def _require_non_negative_int(value: int | None, field_name: str) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be greater than or equal to 0")
    return value


class RunNotFoundError(LookupError):
    """Raised when a persisted run cannot be found."""

    def __init__(self, run_id: str) -> None:
        self.run_id = _require_non_empty_string(run_id, "run_id")
        super().__init__(f"Unknown run_id: {self.run_id}")


class ChatNotFoundError(LookupError):
    """Raised when a persisted chat cannot be found."""

    def __init__(self, chat_id: str) -> None:
        self.chat_id = _require_non_empty_string(chat_id, "chat_id")
        super().__init__(f"Unknown chat_id: {self.chat_id}")


@dataclass(slots=True)
class RunSummary:
    run_id: str
    session_id: str
    agent_id: str
    dataset_path: str
    status: RunState | str
    created_at: str
    updated_at: str

    def __post_init__(self) -> None:
        self.run_id = _require_non_empty_string(self.run_id, "run_id")
        self.session_id = _require_non_empty_string(self.session_id, "session_id")
        self.agent_id = _require_non_empty_string(self.agent_id, "agent_id")
        self.dataset_path = _require_non_empty_string(self.dataset_path, "dataset_path")
        self.status = RunState(self.status)
        self.created_at = _require_non_empty_string(self.created_at, "created_at")
        self.updated_at = _require_non_empty_string(self.updated_at, "updated_at")


@dataclass(slots=True)
class RunDetail:
    run_id: str
    session_id: str
    agent_id: str
    status: RunState | str
    created_at: str
    updated_at: str
    dataset_profile: DatasetProfile | None = None
    result: AgentResult | None = None
    error: RunError | None = None
    artifact_manifest: ArtifactManifest | None = None

    def __post_init__(self) -> None:
        self.run_id = _require_non_empty_string(self.run_id, "run_id")
        self.session_id = _require_non_empty_string(self.session_id, "session_id")
        self.agent_id = _require_non_empty_string(self.agent_id, "agent_id")
        self.status = RunState(self.status)
        self.created_at = _require_non_empty_string(self.created_at, "created_at")
        self.updated_at = _require_non_empty_string(self.updated_at, "updated_at")
        if self.dataset_profile is not None and not isinstance(self.dataset_profile, DatasetProfile):
            raise TypeError("dataset_profile must be a DatasetProfile instance")
        if self.result is not None and not isinstance(self.result, AgentResult):
            raise TypeError("result must be an AgentResult instance")
        if self.error is not None and not isinstance(self.error, RunError):
            raise TypeError("error must be a RunError instance")
        if self.artifact_manifest is not None and not isinstance(self.artifact_manifest, ArtifactManifest):
            raise TypeError("artifact_manifest must be an ArtifactManifest instance")


@dataclass(slots=True)
class ArtifactListItem:
    name: str
    type: str
    path: str
    run_id: str
    size_bytes: int | None = None

    def __post_init__(self) -> None:
        self.name = _require_non_empty_string(self.name, "name")
        self.type = _require_non_empty_string(self.type, "type")
        self.path = _require_non_empty_string(self.path, "path")
        self.run_id = _require_non_empty_string(self.run_id, "run_id")
        self.size_bytes = _require_non_negative_int(self.size_bytes, "size_bytes")


@dataclass(slots=True)
class ChatMessage:
    message_id: str
    role: str
    content: str
    created_at: str
    run_id: str | None = None
    status: str | None = None
    result: AgentResult | None = None
    error: RunError | None = None

    def __post_init__(self) -> None:
        self.message_id = _require_non_empty_string(self.message_id, "message_id")
        self.role = _require_non_empty_string(self.role, "role")
        if self.role not in {"user", "assistant"}:
            raise ValueError("role must be user or assistant")
        self.content = _require_non_empty_string(self.content, "content")
        self.created_at = _require_non_empty_string(self.created_at, "created_at")
        self.run_id = _normalize_optional_string(self.run_id, "run_id")
        self.status = _normalize_optional_string(self.status, "status")
        if self.result is not None and not isinstance(self.result, AgentResult):
            raise TypeError("result must be an AgentResult instance")
        if self.error is not None and not isinstance(self.error, RunError):
            raise TypeError("error must be a RunError instance")


@dataclass(slots=True)
class ChatSummary:
    chat_id: str
    agent_id: str
    dataset_path: str
    title: str
    created_at: str
    updated_at: str
    latest_run_id: str | None = None
    message_count: int = 0

    def __post_init__(self) -> None:
        self.chat_id = _require_non_empty_string(self.chat_id, "chat_id")
        self.agent_id = _require_non_empty_string(self.agent_id, "agent_id")
        self.dataset_path = _require_non_empty_string(self.dataset_path, "dataset_path")
        self.title = _require_non_empty_string(self.title, "title")
        self.created_at = _require_non_empty_string(self.created_at, "created_at")
        self.updated_at = _require_non_empty_string(self.updated_at, "updated_at")
        self.latest_run_id = _normalize_optional_string(self.latest_run_id, "latest_run_id")
        message_count = _require_non_negative_int(self.message_count, "message_count")
        self.message_count = 0 if message_count is None else message_count


@dataclass(slots=True)
class ChatDetail:
    chat_id: str
    agent_id: str
    dataset_path: str
    title: str
    created_at: str
    updated_at: str
    messages: list[ChatMessage] = field(default_factory=list)
    run_ids: list[str] = field(default_factory=list)
    latest_run_id: str | None = None

    def __post_init__(self) -> None:
        self.chat_id = _require_non_empty_string(self.chat_id, "chat_id")
        self.agent_id = _require_non_empty_string(self.agent_id, "agent_id")
        self.dataset_path = _require_non_empty_string(self.dataset_path, "dataset_path")
        self.title = _require_non_empty_string(self.title, "title")
        self.created_at = _require_non_empty_string(self.created_at, "created_at")
        self.updated_at = _require_non_empty_string(self.updated_at, "updated_at")
        self.messages = list(self.messages)
        for message in self.messages:
            if not isinstance(message, ChatMessage):
                raise TypeError("messages must contain ChatMessage instances")
        self.run_ids = [_require_non_empty_string(run_id, "run_ids[]") for run_id in self.run_ids]
        self.latest_run_id = _normalize_optional_string(self.latest_run_id, "latest_run_id")
