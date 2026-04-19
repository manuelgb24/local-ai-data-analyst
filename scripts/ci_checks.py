"""Repo-local CI/release check runner for Phase 7."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

PYTEST_BASE_COMMAND = (sys.executable, "-m", "pytest")


def resolve_npm_executable() -> str:
    return "npm.cmd" if os.name == "nt" else "npm"


WEB_PREFIX_COMMAND = (resolve_npm_executable(), "--prefix", "interfaces/web")


class CheckFailure(RuntimeError):
    """Raised when a CI/release lane cannot be validated."""

    def __init__(self, message: str, *, exit_code: int = 1) -> None:
        super().__init__(message)
        self.exit_code = int(exit_code)


@dataclass(frozen=True, slots=True)
class CommandSpec:
    label: str
    args: tuple[str, ...]
    fail_on_skip: bool = False


Runner = Callable[..., subprocess.CompletedProcess[str]]


PYTHON_COMMAND_SPECS: tuple[CommandSpec, ...] = (
    CommandSpec("python unit", PYTEST_BASE_COMMAND + ("tests/unit", "-q")),
    CommandSpec("python integration", PYTEST_BASE_COMMAND + ("tests/integration", "-q")),
    CommandSpec("python e2e", PYTEST_BASE_COMMAND + ("tests/e2e", "-q")),
)

WEB_COMMAND_SPECS: tuple[CommandSpec, ...] = (
    CommandSpec("web build", WEB_PREFIX_COMMAND + ("run", "build")),
    CommandSpec("web e2e", WEB_PREFIX_COMMAND + ("run", "test:e2e")),
)

SMOKE_COMMAND_SPECS: tuple[CommandSpec, ...] = (
    CommandSpec(
        "smoke ollama adapter",
        PYTEST_BASE_COMMAND + ("tests/smoke/test_ollama_adapter.py", "-q", "-rs"),
        fail_on_skip=True,
    ),
    CommandSpec(
        "smoke real cli workflow",
        PYTEST_BASE_COMMAND + ("tests/smoke/test_real_cli_workflow.py", "-q", "-rs"),
        fail_on_skip=True,
    ),
)


def resolve_command_specs(mode: str) -> tuple[CommandSpec, ...]:
    normalized_mode = str(mode).strip().lower()
    if normalized_mode == "python":
        return PYTHON_COMMAND_SPECS
    if normalized_mode == "web":
        return WEB_COMMAND_SPECS
    if normalized_mode == "smoke":
        return SMOKE_COMMAND_SPECS
    raise ValueError(f"Unsupported mode: {mode}")


def get_provider_health():
    from observability import build_default_operational_readiness_service

    return build_default_operational_readiness_service().get_provider_health()


def ensure_smoke_prerequisites(provider_health=None) -> None:
    provider = provider_health or get_provider_health()
    issues: list[str] = []

    if not provider.binary_available:
        issues.append("El binario `ollama` no está disponible en PATH.")
    if not provider.reachable:
        issues.append(f"Ollama no responde en {provider.endpoint}.")
    if not provider.model_available:
        issues.append(f"El modelo requerido no está disponible: {provider.model}.")

    issues.extend(provider.details)
    unique_issues = list(dict.fromkeys(issues))
    if unique_issues:
        formatted = "\n- ".join(unique_issues)
        raise CheckFailure(f"Smoke prerequisites not satisfied:\n- {formatted}")


def output_contains_skips(output: str) -> bool:
    normalized = str(output)
    lowered = normalized.lower()
    return "SKIPPED [" in normalized or " skipped in " in lowered


def run_command(spec: CommandSpec, *, runner: Runner = subprocess.run) -> None:
    print(f"$ {' '.join(spec.args)}")
    completed = runner(spec.args, cwd=ROOT_DIR, text=True, capture_output=True)

    if completed.stdout:
        print(completed.stdout, end="" if completed.stdout.endswith("\n") else "\n")
    if completed.stderr:
        print(completed.stderr, file=sys.stderr, end="" if completed.stderr.endswith("\n") else "\n")

    if completed.returncode != 0:
        raise CheckFailure(
            f"{spec.label} failed with exit code {completed.returncode}",
            exit_code=completed.returncode,
        )

    if spec.fail_on_skip and output_contains_skips(f"{completed.stdout}\n{completed.stderr}"):
        raise CheckFailure(f"{spec.label} reported skipped tests; smoke lane must run against a ready host.")


def run_mode(mode: str) -> None:
    normalized_mode = str(mode).strip().lower()
    if normalized_mode == "smoke":
        ensure_smoke_prerequisites()

    for spec in resolve_command_specs(normalized_mode):
        run_command(spec)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run repo-local CI/release check lanes.")
    parser.add_argument(
        "mode",
        choices=("python", "web", "smoke"),
        help="Lane to execute: python, web, or smoke.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        run_mode(args.mode)
    except CheckFailure as error:
        print(f"ci_checks failed: {error}", file=sys.stderr)
        return error.exit_code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
