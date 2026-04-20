"""Serialization helpers for persisted run records and API responses."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any

from application import (
    AgentResult,
    ArtifactManifest,
    ChartReference,
    DatasetColumn,
    DatasetProfile,
    RunError,
    RunRequest,
    SqlTraceEntry,
    TableResult,
)

from .models import RunRecord


def to_jsonable(value: Any) -> Any:
    """Recursively convert dataclasses and enums into JSON-safe structures."""

    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {field.name: to_jsonable(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    return str(value)


def deserialize_run_record(payload: dict[str, Any]) -> RunRecord:
    """Restore a RunRecord from persisted JSON payload."""

    request_payload = dict(payload["request"])
    request = RunRequest(
        agent_id=request_payload["agent_id"],
        dataset_path=request_payload["dataset_path"],
        user_prompt=request_payload["user_prompt"],
        session_id=request_payload.get("session_id"),
        conversation_context=list(request_payload.get("conversation_context", [])),
    )

    dataset_profile_payload = payload.get("dataset_profile")
    result_payload = payload.get("result")
    error_payload = payload.get("error")

    return RunRecord(
        run_id=str(payload["run_id"]),
        session_id=str(payload["session_id"]),
        request=request,
        state=str(payload["state"]),
        state_history=[str(item) for item in payload.get("state_history", [])],
        created_at=str(payload["created_at"]),
        updated_at=str(payload["updated_at"]),
        dataset_profile=None if dataset_profile_payload is None else _deserialize_dataset_profile(dataset_profile_payload),
        result=None if result_payload is None else _deserialize_agent_result(result_payload),
        error=None if error_payload is None else _deserialize_run_error(error_payload),
    )


def _deserialize_dataset_profile(payload: dict[str, Any]) -> DatasetProfile:
    return DatasetProfile(
        source_path=str(payload["source_path"]),
        format=str(payload["format"]),
        table_name=str(payload["table_name"]),
        schema=[_deserialize_dataset_column(item) for item in payload.get("schema", [])],
        row_count=int(payload["row_count"]),
        nulls=None if payload.get("nulls") is None else {str(key): int(value) for key, value in payload["nulls"].items()},
        sample=None if payload.get("sample") is None else list(payload["sample"]),
    )


def _deserialize_dataset_column(payload: dict[str, Any]) -> DatasetColumn:
    return DatasetColumn(
        name=str(payload["name"]),
        type=str(payload["type"]),
    )


def _deserialize_agent_result(payload: dict[str, Any]) -> AgentResult:
    return AgentResult(
        narrative=str(payload["narrative"]),
        findings=[str(item) for item in payload.get("findings", [])],
        sql_trace=[_deserialize_sql_trace_entry(item) for item in payload.get("sql_trace", [])],
        tables=[_deserialize_table_result(item) for item in payload.get("tables", [])],
        charts=[_deserialize_chart_reference(item) for item in payload.get("charts", [])],
        artifact_manifest=_deserialize_artifact_manifest(payload["artifact_manifest"]),
        recommendations=None
        if payload.get("recommendations") is None
        else [str(item) for item in payload.get("recommendations", [])],
    )


def _deserialize_sql_trace_entry(payload: dict[str, Any]) -> SqlTraceEntry:
    return SqlTraceEntry(
        statement=str(payload["statement"]),
        status=str(payload["status"]),
        purpose=None if payload.get("purpose") is None else str(payload["purpose"]),
        rows_returned=None if payload.get("rows_returned") is None else int(payload["rows_returned"]),
    )


def _deserialize_table_result(payload: dict[str, Any]) -> TableResult:
    return TableResult(
        name=str(payload["name"]),
        rows=list(payload.get("rows", [])),
    )


def _deserialize_chart_reference(payload: dict[str, Any]) -> ChartReference:
    return ChartReference(
        name=str(payload["name"]),
        path=None if payload.get("path") is None else str(payload["path"]),
        chart_type=str(payload.get("chart_type", "bar")),
        title=None if payload.get("title") is None else str(payload["title"]),
        x_key=None if payload.get("x_key") is None else str(payload["x_key"]),
        y_key=None if payload.get("y_key") is None else str(payload["y_key"]),
        data=list(payload.get("data", [])),
    )


def _deserialize_artifact_manifest(payload: dict[str, Any]) -> ArtifactManifest:
    return ArtifactManifest(
        run_id=str(payload["run_id"]),
        response_path=None if payload.get("response_path") is None else str(payload["response_path"]),
        table_paths=[str(item) for item in payload.get("table_paths", [])],
        chart_paths=[str(item) for item in payload.get("chart_paths", [])],
    )


def _deserialize_run_error(payload: dict[str, Any]) -> RunError:
    return RunError(
        code=str(payload["code"]),
        message=str(payload["message"]),
        stage=str(payload["stage"]),
        details=None if payload.get("details") is None else dict(payload["details"]),
    )


def deserialize_agent_result(payload: dict[str, Any]) -> AgentResult:
    return _deserialize_agent_result(payload)


def deserialize_run_error(payload: dict[str, Any]) -> RunError:
    return _deserialize_run_error(payload)
