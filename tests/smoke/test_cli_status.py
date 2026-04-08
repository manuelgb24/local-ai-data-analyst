from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.smoke._ollama_ready import require_installed_model, require_ready_ollama


REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.smoke
def test_cli_status_reports_ready_json_with_real_ollama() -> None:
    require_ready_ollama()
    require_installed_model()

    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(REPO_ROOT) if not existing_pythonpath else os.pathsep.join([str(REPO_ROOT), existing_pythonpath])
    )
    env["PYTHONUTF8"] = "1"

    completed = subprocess.run(
        [sys.executable, "-m", "interfaces.cli", "status", "--json"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
    )

    if completed.returncode != 0:
        pytest.fail(
            f"`status --json` devolvió exit code {completed.returncode}. "
            f"Stdout: {completed.stdout} Stderr: {completed.stderr}"
        )

    payload = json.loads(completed.stdout)

    assert payload["ready"] is True
    assert payload["application"]["ready"] is True
    assert payload["provider"]["ready"] is True
    assert payload["provider"]["model"] == "deepseek-r1:8b"
