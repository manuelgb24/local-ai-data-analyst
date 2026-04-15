"""Serialization helpers for API responses."""

from __future__ import annotations

from typing import Any

from runtime.serialization import to_jsonable


def serialize_response(value: Any) -> Any:
    """Serialize domain objects into API-safe JSON structures."""

    return to_jsonable(value)


def build_api_error(
    *,
    code: str,
    message: str,
    status: int,
    details: dict[str, Any] | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "code": str(code),
        "message": str(message),
        "status": int(status),
    }
    if details is not None:
        payload["details"] = serialize_response(details)
    if trace_id is not None:
        payload["trace_id"] = str(trace_id)
    return payload

