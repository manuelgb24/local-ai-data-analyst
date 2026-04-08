from pathlib import Path

import pytest

from datetime import date

from application import ErrorStage, RunError, RunRequest
from data.dataset_preparer import LocalDatasetPreparer, build_table_name, detect_dataset_format


def build_request(dataset_path: str) -> RunRequest:
    return RunRequest(
        agent_id="data_analyst",
        dataset_path=dataset_path,
        user_prompt="Resume el dataset",
    )


def test_detect_dataset_format_accepts_supported_extensions() -> None:
    assert detect_dataset_format("sample.csv") == "csv"
    assert detect_dataset_format("sample.xlsx") == "xlsx"
    assert detect_dataset_format("sample.parquet") == "parquet"


def test_detect_dataset_format_rejects_unsupported_extensions() -> None:
    with pytest.raises(RunError, match="dataset_unsupported_format"):
        detect_dataset_format("sample.txt")


def test_build_table_name_sanitizes_run_identifier() -> None:
    assert build_table_name("Run-123/demo") == "dataset_run_123_demo"


def test_local_dataset_preparer_rejects_missing_path() -> None:
    preparer = LocalDatasetPreparer()

    with pytest.raises(RunError, match="dataset_not_found") as exc_info:
        preparer(build_request("missing.csv"), run_id="run-missing")

    assert exc_info.value.stage is ErrorStage.DATASET_PREPARATION


def test_local_dataset_preparer_rejects_empty_file(repo_tmp_path: Path) -> None:
    dataset_path = repo_tmp_path / "empty.csv"
    dataset_path.write_text("", encoding="utf-8")
    preparer = LocalDatasetPreparer()

    with pytest.raises(RunError, match="dataset_empty") as exc_info:
        preparer(build_request(str(dataset_path)), run_id="run-empty")

    assert exc_info.value.details == {"dataset_path": str(dataset_path), "format": "csv"}


def test_infer_duckdb_type_promotes_int_and_float_to_double() -> None:
    preparer = LocalDatasetPreparer()

    assert preparer._infer_duckdb_type([1, 2.5]) == "DOUBLE"


def test_infer_duckdb_type_promotes_numeric_and_string_to_varchar() -> None:
    preparer = LocalDatasetPreparer()

    assert preparer._infer_duckdb_type([1, "text"]) == "VARCHAR"


def test_infer_duckdb_type_promotes_date_and_string_to_varchar() -> None:
    preparer = LocalDatasetPreparer()

    assert preparer._infer_duckdb_type([date(2024, 1, 1), "text"]) == "VARCHAR"


def test_infer_duckdb_type_keeps_boolean_for_pure_booleans() -> None:
    preparer = LocalDatasetPreparer()

    assert preparer._infer_duckdb_type([True, False, None]) == "BOOLEAN"


def test_promote_duckdb_type_keeps_existing_type_for_none_values() -> None:
    preparer = LocalDatasetPreparer()

    assert preparer._promote_duckdb_type("BIGINT", None) == "BIGINT"
    assert preparer._promote_duckdb_type("DOUBLE", None) == "DOUBLE"
    assert preparer._promote_duckdb_type("DATE", None) == "DATE"
