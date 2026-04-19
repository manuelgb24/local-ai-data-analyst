from __future__ import annotations

import subprocess
import os

import pytest

import scripts.ci_checks as ci_checks
from observability.models import ProveedorHealth


def build_provider_health(
    *,
    binary_available: bool = True,
    reachable: bool = True,
    model_available: bool = True,
    details: list[str] | None = None,
) -> ProveedorHealth:
    return ProveedorHealth(
        proveedor="ollama",
        endpoint="http://127.0.0.1:11434",
        reachable=reachable,
        model="deepseek-r1:8b",
        model_available=model_available,
        binary_available=binary_available,
        binary_path="C:/ollama/ollama.exe" if binary_available else None,
        version="0.0.0" if reachable else None,
        details=details or [],
    )


def test_resolve_command_specs_for_python_mode() -> None:
    specs = ci_checks.resolve_command_specs("python")

    assert [spec.label for spec in specs] == [
        "python unit",
        "python integration",
        "python e2e",
    ]


def test_resolve_command_specs_for_web_mode() -> None:
    specs = ci_checks.resolve_command_specs("web")

    assert specs[0].args[0] == ("npm.cmd" if os.name == "nt" else "npm")
    assert [spec.args[-2:] for spec in specs] == [
        ("run", "build"),
        ("run", "test:e2e"),
    ]


def test_ensure_smoke_prerequisites_fails_when_provider_not_ready() -> None:
    provider_health = build_provider_health(
        reachable=False,
        model_available=False,
        details=["Ollama no responde.", "Falta el modelo."],
    )

    with pytest.raises(ci_checks.CheckFailure, match="Smoke prerequisites not satisfied"):
        ci_checks.ensure_smoke_prerequisites(provider_health)


def test_run_mode_smoke_runs_commands_when_provider_is_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    executed: list[str] = []

    monkeypatch.setattr(ci_checks, "get_provider_health", lambda: build_provider_health())
    monkeypatch.setattr(
        ci_checks,
        "run_command",
        lambda spec, runner=subprocess.run: executed.append(spec.label),
    )

    ci_checks.run_mode("smoke")

    assert executed == [
        "smoke ollama adapter",
        "smoke real cli workflow",
    ]


def test_run_command_fails_when_smoke_output_reports_skips() -> None:
    spec = ci_checks.CommandSpec(
        label="smoke lane",
        args=("python", "-m", "pytest", "tests/smoke/test_example.py", "-q", "-rs"),
        fail_on_skip=True,
    )

    def fake_runner(*args, **kwargs) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout="s\nSKIPPED [1] tests/smoke/test_example.py:1: not ready\n1 skipped in 0.10s\n",
            stderr="",
        )

    with pytest.raises(ci_checks.CheckFailure, match="reported skipped tests"):
        ci_checks.run_command(spec, runner=fake_runner)


def test_main_returns_non_zero_when_a_lane_fails(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(
        ci_checks,
        "run_mode",
        lambda mode: (_ for _ in ()).throw(ci_checks.CheckFailure("lane failed", exit_code=7)),
    )

    exit_code = ci_checks.main(["python"])

    assert exit_code == 7
    assert "ci_checks failed: lane failed" in capsys.readouterr().err
