"""Error classification helpers for product observability."""

from __future__ import annotations

from typing import Any

from application.contracts import ErrorStage, RunError

ERROR_CATEGORY_REQUEST = "request"
ERROR_CATEGORY_DATASET = "dataset"
ERROR_CATEGORY_PROVIDER = "provider"
ERROR_CATEGORY_CORE = "core"


def classify_run_error(error: RunError) -> str:
    """Classify a runtime/application error for support visibility."""

    if not isinstance(error, RunError):
        raise TypeError("error must be a RunError instance")

    if error.stage in {ErrorStage.REQUEST_VALIDATION, ErrorStage.AGENT_RESOLUTION}:
        return ERROR_CATEGORY_REQUEST
    if error.stage is ErrorStage.DATASET_PREPARATION or error.code.startswith("dataset_"):
        return ERROR_CATEGORY_DATASET
    if error.code.startswith("llm_"):
        return ERROR_CATEGORY_PROVIDER
    if error.details and "provider" in error.details:
        return ERROR_CATEGORY_PROVIDER
    return ERROR_CATEGORY_CORE


def ensure_error_category(error: RunError) -> RunError:
    """Mutate a RunError in place so details always include category."""

    if not isinstance(error, RunError):
        raise TypeError("error must be a RunError instance")

    details: dict[str, Any] = dict(error.details or {})
    details.setdefault("category", classify_run_error(error))
    error.details = details
    return error


def build_api_error_details(
    *,
    category: str,
    stage: str | None = None,
    context: dict[str, Any] | None = None,
    **fields: Any,
) -> dict[str, Any]:
    """Build the stable `details` payload for API errors."""

    details: dict[str, Any] = {"category": str(category)}
    if stage is not None:
        details["stage"] = str(stage)
    if context:
        details["context"] = dict(context)
    for key, value in fields.items():
        if value is not None:
            details[str(key)] = value
    return details


__all__ = [
    "ERROR_CATEGORY_CORE",
    "ERROR_CATEGORY_DATASET",
    "ERROR_CATEGORY_PROVIDER",
    "ERROR_CATEGORY_REQUEST",
    "build_api_error_details",
    "classify_run_error",
    "ensure_error_category",
]
