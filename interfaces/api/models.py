"""HTTP request/response payload models for the local API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CreateRunRequestPayload(BaseModel):
    agent_id: str = Field(..., description="Static agent identifier to execute.")
    dataset_path: str = Field(..., description="Manual local path to a csv/xlsx/parquet dataset.")
    user_prompt: str = Field(..., description="Natural-language analysis request.")
    session_id: str | None = Field(default=None, description="Optional session identifier for continuing a session.")


class ApiErrorPayload(BaseModel):
    code: str
    message: str
    status: int
    details: dict[str, Any] | None = None
    trace_id: str | None = None

