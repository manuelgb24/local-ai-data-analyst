"""Data-layer models for dataset preparation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from application.contracts import DatasetProfile


@dataclass(slots=True)
class PreparedDataset:
    """Prepared dataset payload returned by the data layer."""

    dataset_profile: DatasetProfile
    duckdb_context: Any

    def __post_init__(self) -> None:
        if not isinstance(self.dataset_profile, DatasetProfile):
            raise TypeError("dataset_profile must be a DatasetProfile instance")
        if self.duckdb_context is None:
            raise ValueError("duckdb_context must be provided")
