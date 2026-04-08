import pytest

from application import DatasetColumn, DatasetProfile
from data import PreparedDataset


def build_profile() -> DatasetProfile:
    return DatasetProfile(
        source_path="DatasetV1/Walmart_Sales.csv",
        format="csv",
        table_name="dataset_run_001",
        schema=[DatasetColumn(name="store", type="INTEGER")],
        row_count=3,
    )


def test_prepared_dataset_accepts_valid_profile_and_context() -> None:
    prepared = PreparedDataset(dataset_profile=build_profile(), duckdb_context=object())

    assert prepared.dataset_profile.table_name == "dataset_run_001"


def test_prepared_dataset_requires_dataset_profile_instance() -> None:
    with pytest.raises(TypeError, match="dataset_profile"):
        PreparedDataset(dataset_profile="invalid", duckdb_context=object())


def test_prepared_dataset_requires_duckdb_context() -> None:
    with pytest.raises(ValueError, match="duckdb_context"):
        PreparedDataset(dataset_profile=build_profile(), duckdb_context=None)
