from __future__ import annotations

import json
from io import StringIO

from application import ErrorStage, RunError
from observability import (
    bind_context,
    classify_run_error,
    clear_context,
    configure_structured_logging,
    current_context,
    ensure_error_category,
    get_logger,
    log_event,
    reset_context,
)


def parse_log_lines(stream: StringIO) -> list[dict[str, object]]:
    return [json.loads(line) for line in stream.getvalue().splitlines() if line.strip()]


def test_structured_formatter_merges_bound_context_and_event_fields() -> None:
    stream = StringIO()
    clear_context()
    configure_structured_logging(stream=stream, force=True)
    logger = get_logger("tests.observability")

    token = bind_context(trace_id="trace-123", session_id="session-123")
    try:
        log_event(logger, "run_started", run_id="run-123", dataset_path="DatasetV1/demo_business_metrics.csv")
    finally:
        reset_context(token)
        clear_context()

    payload = parse_log_lines(stream)[0]
    assert payload["event"] == "run_started"
    assert payload["trace_id"] == "trace-123"
    assert payload["session_id"] == "session-123"
    assert payload["run_id"] == "run-123"
    assert payload["dataset_path"] == "DatasetV1/demo_business_metrics.csv"


def test_bind_context_restores_previous_values_on_reset() -> None:
    clear_context()
    parent = bind_context(trace_id="trace-parent")
    nested = bind_context(run_id="run-child")

    assert current_context() == {"trace_id": "trace-parent", "run_id": "run-child"}

    reset_context(nested)
    assert current_context() == {"trace_id": "trace-parent"}

    reset_context(parent)
    assert current_context() == {}


def test_classify_run_error_distinguishes_request_dataset_provider_and_core() -> None:
    assert classify_run_error(
        RunError(code="invalid_request", message="bad request", stage=ErrorStage.REQUEST_VALIDATION)
    ) == "request"
    assert classify_run_error(
        RunError(code="dataset_not_found", message="missing dataset", stage=ErrorStage.DATASET_PREPARATION)
    ) == "dataset"
    assert classify_run_error(
        RunError(code="llm_provider_unavailable", message="provider down", stage=ErrorStage.AGENT_EXECUTION)
    ) == "provider"
    assert classify_run_error(
        RunError(code="unexpected_runtime_error", message="boom", stage=ErrorStage.AGENT_EXECUTION)
    ) == "core"


def test_ensure_error_category_adds_missing_category_once() -> None:
    error = RunError(
        code="dataset_not_found",
        message="missing dataset",
        stage=ErrorStage.DATASET_PREPARATION,
        details={"dataset_path": "missing.csv"},
    )

    enriched = ensure_error_category(error)

    assert enriched.details == {
        "dataset_path": "missing.csv",
        "category": "dataset",
    }
