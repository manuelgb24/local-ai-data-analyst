from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from tests.smoke._ollama_ready import require_installed_model, require_ready_ollama


SMOKE_E2E_TIMEOUT_SECONDS = 240.0
REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = REPO_ROOT / "DatasetV1" / "demo_business_metrics.csv"
RUN_ID_PATTERN = re.compile(r"^Run ID: (?P<run_id>.+)$", re.MULTILINE)
SESSION_ID_PATTERN = re.compile(r"^Session ID: (?P<session_id>.+)$", re.MULTILINE)
RESPONSE_ARTIFACT_PATTERN = re.compile(r"^Response artifact: (?P<path>.+)$", re.MULTILINE)
TABLE_ARTIFACT_PATTERN = re.compile(r"^- (?P<path>.+\.json)$", re.MULTILINE)


@pytest.mark.smoke
def test_cli_real_workflow_roundtrip_with_ollama(repo_tmp_path: Path) -> None:
    require_ready_ollama()
    require_installed_model()

    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(REPO_ROOT) if not existing_pythonpath else os.pathsep.join([str(REPO_ROOT), existing_pythonpath])
    )
    env["PYTHONUTF8"] = "1"

    command = [
        sys.executable,
        "-m",
        "interfaces.cli",
        "--agent",
        "data_analyst",
        "--dataset",
        str(DATASET_PATH.resolve()),
        "--prompt",
        "Resume brevemente los hallazgos principales del dataset.",
    ]

    try:
        completed = subprocess.run(
            command,
            cwd=repo_tmp_path,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=SMOKE_E2E_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        pytest.fail(
            "El smoke E2E real de la CLI agotó el timeout "
            f"({SMOKE_E2E_TIMEOUT_SECONDS}s). Stdout parcial: {exc.stdout!r} Stderr parcial: {exc.stderr!r}"
        )

    stdout = completed.stdout
    stderr = completed.stderr

    if completed.returncode != 0:
        if "Error code: llm_provider_unavailable" in stderr:
            pytest.skip(
                "No se pudo completar el workflow real porque Ollama dejó de estar disponible para la CLI real "
                "después del readiness inicial. "
                f"Stderr: {stderr}"
            )
        if "Error code: llm_generation_failed" in stderr:
            pytest.fail(
                "La CLI real alcanzó Ollama pero el modelo fijo del MVP no pudo completar la generación. "
                f"Stderr: {stderr}"
            )
        pytest.fail(
            f"La CLI real terminó con exit code {completed.returncode}. Stdout: {stdout} Stderr: {stderr}"
        )

    run_id_match = RUN_ID_PATTERN.search(stdout)
    session_id_match = SESSION_ID_PATTERN.search(stdout)
    response_match = RESPONSE_ARTIFACT_PATTERN.search(stdout)

    assert session_id_match is not None, stdout
    assert run_id_match is not None, stdout
    assert response_match is not None, stdout

    run_id = run_id_match.group("run_id").strip()
    session_id = session_id_match.group("session_id").strip()
    response_path = Path(response_match.group("path").strip())
    table_paths = [Path(match.group("path").strip()) for match in TABLE_ARTIFACT_PATTERN.finditer(stdout)]

    assert session_id.startswith("session-")
    assert run_id.startswith("run-")
    assert response_path.is_file()
    assert response_path.name == "response.md"
    assert run_id in response_path.parts
    assert "Response artifact:" in stdout
    assert "Table artifacts:" in stdout
    assert table_paths, stdout
    assert all(path.is_file() for path in table_paths)
