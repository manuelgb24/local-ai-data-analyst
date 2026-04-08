"""In-memory run/session tracking for the MVP runtime."""

from __future__ import annotations

from uuid import uuid4

from application.contracts import AgentResult, RunError, RunRequest, RunState

from .models import RunRecord


class InMemoryRunTracker:
    """Tracks run lifecycle in memory for the current process."""

    def __init__(self) -> None:
        self._runs: dict[str, RunRecord] = {}

    def start_run(self, request: RunRequest) -> RunRecord:
        if not isinstance(request, RunRequest):
            raise TypeError("request must be a RunRequest instance")

        record = RunRecord(
            run_id=f"run-{uuid4().hex}",
            session_id=request.session_id or f"session-{uuid4().hex}",
            request=request,
            state=RunState.CREATED,
        )
        self._runs[record.run_id] = record
        return record

    def mark_preparing_dataset(self, run_id: str) -> RunRecord:
        return self._transition(run_id, RunState.PREPARING_DATASET)

    def mark_running_agent(self, run_id: str) -> RunRecord:
        return self._transition(run_id, RunState.RUNNING_AGENT)

    def mark_succeeded(self, run_id: str, result: AgentResult) -> RunRecord:
        if not isinstance(result, AgentResult):
            raise TypeError("result must be an AgentResult instance")

        record = self._transition(run_id, RunState.SUCCEEDED)
        record.result = result
        record.error = None
        return record

    def mark_failed(self, run_id: str, error: RunError) -> RunRecord:
        if not isinstance(error, RunError):
            raise TypeError("error must be a RunError instance")

        record = self._transition(run_id, RunState.FAILED)
        record.error = error
        record.result = None
        return record

    def get(self, run_id: str) -> RunRecord:
        try:
            return self._runs[run_id]
        except KeyError as exc:
            raise KeyError(f"Unknown run_id: {run_id}") from exc

    def _transition(self, run_id: str, state: RunState) -> RunRecord:
        record = self.get(run_id)
        record.state = state
        record.state_history.append(state)
        return record
