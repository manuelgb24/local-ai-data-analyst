import pytest

from application.contracts import ErrorStage, RunError, RunState


def test_run_error_accepts_allowed_stage_values() -> None:
    error = RunError(
        code="dataset_not_found",
        message="No se encontró el dataset",
        stage="dataset_preparation",
        details={"dataset_path": "missing.csv"},
    )

    assert error.stage is ErrorStage.DATASET_PREPARATION
    assert error.details == {"dataset_path": "missing.csv"}


def test_run_error_rejects_unknown_stage() -> None:
    with pytest.raises(ValueError, match="unknown_stage"):
        RunError(
            code="invalid_stage",
            message="Stage inválido",
            stage="unknown_stage",
        )


def test_run_state_contains_only_mvp_states() -> None:
    assert {state.value for state in RunState} == {
        "created",
        "preparing_dataset",
        "running_agent",
        "succeeded",
        "failed",
    }
