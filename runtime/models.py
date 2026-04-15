"""Runtime-only models for run coordination and tracking."""

from __future__ import annotations

from dataclasses import dataclass, field

from application.contracts import AgentResult, DatasetProfile, RunError, RunRequest, RunState


def _require_non_empty_string(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty string")

    return normalized


@dataclass(slots=True)
class RunRecord:
    """In-memory tracking snapshot for a single run."""

    run_id: str
    session_id: str
    request: RunRequest
    state: RunState
    state_history: list[RunState] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    dataset_profile: DatasetProfile | None = None
    result: AgentResult | None = None
    error: RunError | None = None

    def __post_init__(self) -> None:
        self.run_id = _require_non_empty_string(self.run_id, "run_id")
        self.session_id = _require_non_empty_string(self.session_id, "session_id")
        if not isinstance(self.request, RunRequest):
            raise TypeError("request must be a RunRequest instance")
        self.state = RunState(self.state)
        self.created_at = _require_non_empty_string(self.created_at, "created_at")
        self.updated_at = _require_non_empty_string(self.updated_at, "updated_at")

        self.state_history = list(self.state_history) if self.state_history else [self.state]
        self.state_history = [RunState(item) for item in self.state_history]
        if self.dataset_profile is not None and not isinstance(self.dataset_profile, DatasetProfile):
            raise TypeError("dataset_profile must be a DatasetProfile instance")
        if self.result is not None and not isinstance(self.result, AgentResult):
            raise TypeError("result must be an AgentResult instance")
        if self.error is not None and not isinstance(self.error, RunError):
            raise TypeError("error must be a RunError instance")
