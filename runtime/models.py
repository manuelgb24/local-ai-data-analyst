"""Runtime-only models for run coordination and tracking."""

from __future__ import annotations

from dataclasses import dataclass, field

from application.contracts import AgentResult, RunError, RunRequest, RunState


@dataclass(slots=True)
class RunRecord:
    """In-memory tracking snapshot for a single run."""

    run_id: str
    session_id: str
    request: RunRequest
    state: RunState
    state_history: list[RunState] = field(default_factory=list)
    result: AgentResult | None = None
    error: RunError | None = None

    def __post_init__(self) -> None:
        if not self.run_id.strip():
            raise ValueError("run_id must be a non-empty string")
        if not self.session_id.strip():
            raise ValueError("session_id must be a non-empty string")
        if not isinstance(self.request, RunRequest):
            raise TypeError("request must be a RunRequest instance")
        if not isinstance(self.state, RunState):
            raise TypeError("state must be a RunState instance")

        self.state_history = list(self.state_history) if self.state_history else [self.state]

        if not all(isinstance(item, RunState) for item in self.state_history):
            raise TypeError("state_history must contain RunState values")
        if self.result is not None and not isinstance(self.result, AgentResult):
            raise TypeError("result must be an AgentResult instance")
        if self.error is not None and not isinstance(self.error, RunError):
            raise TypeError("error must be a RunError instance")
