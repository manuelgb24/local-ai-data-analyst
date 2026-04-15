"""Application use cases for persisted local run history."""

from __future__ import annotations

from typing import Protocol

from .api_contracts import ArtifactListItem, RunDetail, RunSummary


class RunHistoryStore(Protocol):
    def list_runs(self) -> list[RunSummary]: ...

    def get_run(self, run_id: str) -> RunDetail: ...

    def list_artifacts(self, run_id: str) -> list[ArtifactListItem]: ...


class ListRunsUseCase:
    """Return the persisted local run history for API/UI consumers."""

    def __init__(self, store: RunHistoryStore) -> None:
        self._store = store

    def execute(self) -> list[RunSummary]:
        return self._store.list_runs()


class GetRunUseCase:
    """Return the persisted detail for a single run."""

    def __init__(self, store: RunHistoryStore) -> None:
        self._store = store

    def execute(self, run_id: str) -> RunDetail:
        return self._store.get_run(run_id)


class ListRunArtifactsUseCase:
    """Return the persisted artifact references for a single run."""

    def __init__(self, store: RunHistoryStore) -> None:
        self._store = store

    def execute(self, run_id: str) -> list[ArtifactListItem]:
        return self._store.list_artifacts(run_id)

