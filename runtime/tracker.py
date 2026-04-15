"""In-memory run/session tracking for the MVP runtime."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from uuid import uuid4

from application.contracts import AgentResult, DatasetProfile, RunError, RunRequest, RunState

from .models import RunRecord

RunRecordCallback = Callable[[RunRecord], None]


def _utcnow_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


class InMemoryRunTracker:
    """Tracks run lifecycle in memory for the current process."""

    def __init__(self, on_change: RunRecordCallback | None = None) -> None:
        self._runs: dict[str, RunRecord] = {}
        self._on_change = on_change

    def start_run(self, request: RunRequest) -> RunRecord:
        if not isinstance(request, RunRequest):
            raise TypeError("request must be a RunRequest instance")

        timestamp = _utcnow_timestamp()
        record = RunRecord(
            run_id=f"run-{uuid4().hex}",
            session_id=request.session_id or f"session-{uuid4().hex}",
            request=request,
            state=RunState.CREATED,
            created_at=timestamp,
            updated_at=timestamp,
        )
        self._runs[record.run_id] = record
        self._notify_change(record)
        return record

    def mark_preparing_dataset(self, run_id: str) -> RunRecord:
        record = self._transition(run_id, RunState.PREPARING_DATASET)
        self._notify_change(record)
        return record

    def mark_running_agent(self, run_id: str, dataset_profile: DatasetProfile | None = None) -> RunRecord:
        if dataset_profile is not None and not isinstance(dataset_profile, DatasetProfile):
            raise TypeError("dataset_profile must be a DatasetProfile instance")

        record = self._transition(run_id, RunState.RUNNING_AGENT)
        if dataset_profile is not None:
            record.dataset_profile = dataset_profile
        self._notify_change(record)
        return record

    def mark_succeeded(self, run_id: str, result: AgentResult) -> RunRecord:
        if not isinstance(result, AgentResult):
            raise TypeError("result must be an AgentResult instance")

        record = self._transition(run_id, RunState.SUCCEEDED)
        record.result = result
        record.error = None
        self._notify_change(record)
        return record

    def mark_failed(self, run_id: str, error: RunError) -> RunRecord:
        if not isinstance(error, RunError):
            raise TypeError("error must be a RunError instance")

        record = self._transition(run_id, RunState.FAILED)
        record.error = error
        record.result = None
        self._notify_change(record)
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
        record.updated_at = _utcnow_timestamp()
        return record

    def _notify_change(self, record: RunRecord) -> None:
        if self._on_change is None:
            return
        self._on_change(record)
