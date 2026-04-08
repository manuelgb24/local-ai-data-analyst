"""Shared pytest bootstrap for the repo."""

from __future__ import annotations

import sys
import shutil
from pathlib import Path
from uuid import uuid4

import pytest


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def repo_tmp_path() -> Path:
    """Create a writable temporary directory inside the repo workspace."""

    temp_root = ROOT / ".tmp_pytest"
    temp_root.mkdir(parents=True, exist_ok=True)
    directory = temp_root / uuid4().hex
    directory.mkdir(parents=True, exist_ok=False)

    try:
        yield directory
    finally:
        shutil.rmtree(directory, ignore_errors=True)
