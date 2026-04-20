"""Core MVP contracts for the vertical slice."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Any, ClassVar


_URL_SCHEME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://")


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


def _normalize_conversation_context(value: list[dict[str, str]] | None) -> list[dict[str, str]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise TypeError("conversation_context must be a list")

    normalized: list[dict[str, str]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise TypeError(f"conversation_context[{index}] must be an object")
        role = _require_non_empty_string(str(item.get("role", "")), f"conversation_context[{index}].role")
        content = _require_non_empty_string(str(item.get("content", "")), f"conversation_context[{index}].content")
        if role not in {"user", "assistant"}:
            raise ValueError(f"conversation_context[{index}].role must be user or assistant")
        normalized.append({"role": role, "content": content})
    return normalized


def _validate_local_path(path: str, field_name: str) -> str:
    normalized = _require_non_empty_string(path, field_name)
    if _URL_SCHEME_PATTERN.match(normalized):
        raise ValueError(f"{field_name} must point to a local file path, not a URL")
    return normalized


def _require_non_negative_int(value: int, field_name: str) -> int:
    if not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be greater than or equal to 0")
    return value


class RunState(Enum):
    CREATED = "created"
    PREPARING_DATASET = "preparing_dataset"
    RUNNING_AGENT = "running_agent"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ErrorStage(Enum):
    REQUEST_VALIDATION = "request_validation"
    DATASET_PREPARATION = "dataset_preparation"
    AGENT_RESOLUTION = "agent_resolution"
    AGENT_EXECUTION = "agent_execution"
    ARTIFACT_PERSISTENCE = "artifact_persistence"


class SqlTraceStatus(Enum):
    OK = "ok"
    ERROR = "error"


@dataclass(slots=True)
class DatasetColumn:
    name: str
    type: str

    def __post_init__(self) -> None:
        self.name = _require_non_empty_string(self.name, "name")
        self.type = _require_non_empty_string(self.type, "type")


@dataclass(slots=True)
class SqlTraceEntry:
    statement: str
    status: SqlTraceStatus | str
    purpose: str | None = None
    rows_returned: int | None = None

    def __post_init__(self) -> None:
        self.statement = _require_non_empty_string(self.statement, "statement")
        self.status = SqlTraceStatus(self.status)
        self.purpose = _normalize_optional_string(self.purpose, "purpose")
        if self.rows_returned is not None:
            self.rows_returned = _require_non_negative_int(self.rows_returned, "rows_returned")


@dataclass(slots=True)
class TableResult:
    name: str
    rows: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.name = _require_non_empty_string(self.name, "name")
        self.rows = list(self.rows)


@dataclass(slots=True)
class ChartReference:
    name: str
    path: str | None = None
    chart_type: str = "bar"
    title: str | None = None
    x_key: str | None = None
    y_key: str | None = None
    data: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.name = _require_non_empty_string(self.name, "name")
        if self.path is not None:
            self.path = _require_non_empty_string(self.path, "path")
        self.chart_type = _require_non_empty_string(self.chart_type, "chart_type")
        self.title = _normalize_optional_string(self.title, "title")
        self.x_key = _normalize_optional_string(self.x_key, "x_key")
        self.y_key = _normalize_optional_string(self.y_key, "y_key")
        self.data = [dict(row) for row in self.data]


@dataclass(slots=True)
class RunRequest:
    SUPPORTED_FORMATS: ClassVar[frozenset[str]] = frozenset({"csv", "xlsx", "parquet"})

    agent_id: str
    dataset_path: str
    user_prompt: str
    session_id: str | None = None
    conversation_context: list[dict[str, str]] | None = None

    def __post_init__(self) -> None:
        self.agent_id = _require_non_empty_string(self.agent_id, "agent_id")
        self.dataset_path = _validate_local_path(self.dataset_path, "dataset_path")
        self.user_prompt = _require_non_empty_string(self.user_prompt, "user_prompt")
        self.session_id = _normalize_optional_string(self.session_id, "session_id")
        self.conversation_context = _normalize_conversation_context(self.conversation_context)

        extension = self.dataset_path.rsplit(".", maxsplit=1)
        if len(extension) != 2 or extension[1].lower() not in self.SUPPORTED_FORMATS:
            raise ValueError("dataset_path must use a supported format: csv, xlsx, parquet")


@dataclass(slots=True)
class DatasetProfile:
    SUPPORTED_FORMATS: ClassVar[frozenset[str]] = RunRequest.SUPPORTED_FORMATS

    source_path: str
    format: str
    table_name: str
    schema: list[DatasetColumn]
    row_count: int
    nulls: dict[str, int] | None = None
    sample: list[dict[str, Any]] | None = None

    def __post_init__(self) -> None:
        self.source_path = _validate_local_path(self.source_path, "source_path")
        self.format = _require_non_empty_string(self.format, "format").lower()
        if self.format not in self.SUPPORTED_FORMATS:
            raise ValueError("format must be one of: csv, xlsx, parquet")
        self.table_name = _require_non_empty_string(self.table_name, "table_name")
        self.schema = list(self.schema)
        if not self.schema:
            raise ValueError("schema must contain at least one column")
        self.row_count = _require_non_negative_int(self.row_count, "row_count")
        if self.nulls is not None:
            self.nulls = {str(key): _require_non_negative_int(value, f"nulls[{key}]") for key, value in self.nulls.items()}
        if self.sample is not None:
            self.sample = list(self.sample)


@dataclass(slots=True)
class ArtifactManifest:
    run_id: str
    response_path: str | None = None
    table_paths: list[str] = field(default_factory=list)
    chart_paths: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.run_id = _require_non_empty_string(self.run_id, "run_id")
        self.response_path = _normalize_optional_string(self.response_path, "response_path")
        self.table_paths = [_require_non_empty_string(path, "table_paths[]") for path in self.table_paths]
        self.chart_paths = [_require_non_empty_string(path, "chart_paths[]") for path in self.chart_paths]


@dataclass(slots=True)
class AgentExecutionContext:
    run_id: str
    session_id: str
    dataset_profile: DatasetProfile
    duckdb_context: Any
    output_dir: str

    def __post_init__(self) -> None:
        self.run_id = _require_non_empty_string(self.run_id, "run_id")
        self.session_id = _require_non_empty_string(self.session_id, "session_id")
        if not isinstance(self.dataset_profile, DatasetProfile):
            raise TypeError("dataset_profile must be a DatasetProfile instance")
        if self.duckdb_context is None:
            raise ValueError("duckdb_context must be provided")
        self.output_dir = _require_non_empty_string(self.output_dir, "output_dir")


@dataclass(slots=True)
class AgentResult:
    narrative: str
    findings: list[str]
    sql_trace: list[SqlTraceEntry]
    tables: list[TableResult]
    charts: list[ChartReference]
    artifact_manifest: ArtifactManifest
    recommendations: list[str] | None = None

    def __post_init__(self) -> None:
        self.narrative = _require_non_empty_string(self.narrative, "narrative")
        self.findings = [_require_non_empty_string(item, "findings[]") for item in self.findings]
        self.sql_trace = list(self.sql_trace)
        self.tables = list(self.tables)
        self.charts = list(self.charts)
        if not isinstance(self.artifact_manifest, ArtifactManifest):
            raise TypeError("artifact_manifest must be an ArtifactManifest instance")
        if self.recommendations is not None:
            self.recommendations = [
                _require_non_empty_string(item, "recommendations[]") for item in self.recommendations
            ]


@dataclass(slots=True)
class RunError(Exception):
    code: str
    message: str
    stage: ErrorStage | str
    details: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        self.code = _require_non_empty_string(self.code, "code")
        self.message = _require_non_empty_string(self.message, "message")
        self.stage = ErrorStage(self.stage)
        if self.details is not None:
            self.details = dict(self.details)
        Exception.__init__(self, f"{self.code}: {self.message}")
