"""Filesystem-backed persisted run metadata for the local API."""

from __future__ import annotations

import json
from pathlib import Path

from application import ArtifactListItem, RunDetail, RunNotFoundError, RunSummary
from runtime.models import RunRecord
from runtime.serialization import deserialize_run_record, to_jsonable


RUN_METADATA_FILENAME = "run.json"


class FilesystemRunMetadataStore:
    """Persist and query local run metadata next to each run artifact directory."""

    def __init__(self, artifacts_root: str | Path = "artifacts/runs") -> None:
        self._artifacts_root = Path(artifacts_root)

    def save(self, record: RunRecord) -> None:
        if not isinstance(record, RunRecord):
            raise TypeError("record must be a RunRecord instance")

        metadata_path = self._metadata_path(record.run_id)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(
            json.dumps(to_jsonable(record), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def list_runs(self) -> list[RunSummary]:
        records = [self._read_record(path) for path in self._iter_metadata_paths()]
        records.sort(key=lambda item: (item.updated_at, item.created_at, item.run_id), reverse=True)
        return [self._to_run_summary(record) for record in records]

    def get_run(self, run_id: str) -> RunDetail:
        record = self.load_record(run_id)
        artifact_manifest = record.result.artifact_manifest if record.result is not None else None
        return RunDetail(
            run_id=record.run_id,
            session_id=record.session_id,
            agent_id=record.request.agent_id,
            status=record.state,
            created_at=record.created_at,
            updated_at=record.updated_at,
            dataset_profile=record.dataset_profile,
            result=record.result,
            error=record.error,
            artifact_manifest=artifact_manifest,
        )

    def list_artifacts(self, run_id: str) -> list[ArtifactListItem]:
        record = self.load_record(run_id)
        if record.result is None:
            return []

        manifest = record.result.artifact_manifest
        artifacts: list[ArtifactListItem] = []

        if manifest.response_path:
            artifacts.append(self._build_artifact_item(run_id, manifest.response_path, artifact_type="response"))
        artifacts.extend(self._build_artifact_item(run_id, path, artifact_type="table") for path in manifest.table_paths)
        artifacts.extend(self._build_artifact_item(run_id, path, artifact_type="chart") for path in manifest.chart_paths)
        return artifacts

    def load_record(self, run_id: str) -> RunRecord:
        metadata_path = self._metadata_path(run_id)
        if not metadata_path.exists():
            raise RunNotFoundError(run_id)
        return self._read_record(metadata_path)

    def _iter_metadata_paths(self) -> list[Path]:
        if not self._artifacts_root.exists():
            return []
        return sorted(path for path in self._artifacts_root.glob(f"*/{RUN_METADATA_FILENAME}") if path.is_file())

    def _read_record(self, metadata_path: Path) -> RunRecord:
        try:
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise RunNotFoundError(metadata_path.parent.name) from exc
        return deserialize_run_record(payload)

    def _metadata_path(self, run_id: str) -> Path:
        normalized_run_id = str(run_id).strip()
        if not normalized_run_id:
            raise ValueError("run_id must be a non-empty string")
        return self._artifacts_root / normalized_run_id / RUN_METADATA_FILENAME

    def _to_run_summary(self, record: RunRecord) -> RunSummary:
        return RunSummary(
            run_id=record.run_id,
            session_id=record.session_id,
            agent_id=record.request.agent_id,
            dataset_path=record.request.dataset_path,
            status=record.state,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def _build_artifact_item(self, run_id: str, path: str, *, artifact_type: str) -> ArtifactListItem:
        artifact_path = Path(path)
        size_bytes = artifact_path.stat().st_size if artifact_path.exists() and artifact_path.is_file() else None
        return ArtifactListItem(
            name=artifact_path.name,
            type=artifact_type,
            path=str(artifact_path),
            run_id=run_id,
            size_bytes=size_bytes,
        )
