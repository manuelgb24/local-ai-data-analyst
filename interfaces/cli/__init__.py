"""CLI interface for the MVP plus local operational status/config commands."""

from __future__ import annotations

import argparse
from dataclasses import asdict, is_dataclass
from enum import Enum
import json
import sys
from pathlib import Path
from typing import Any, TextIO

from application import (
    ErrorStage,
    GetAppConfigUseCase,
    GetOperationalStatusUseCase,
    RunAnalysisUseCase,
    RunError,
    RunRequest,
)
from data import LocalDatasetPreparer
from observability import OperationalReadinessService, ReadinessReport, build_default_operational_readiness_service
from runtime import RuntimeCoordinator, build_default_agent_registry

DEFAULT_ARTIFACTS_ROOT = "artifacts/runs"
_KNOWN_COMMANDS = frozenset({"run", "status", "config"})


def _add_run_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--agent", dest="agent_id", required=True, help="Agent identifier to execute.")
    parser.add_argument("--dataset", dest="dataset_path", required=True, help="Local dataset path.")
    parser.add_argument("--prompt", dest="user_prompt", required=True, help="Natural-language analysis request.")
    parser.add_argument(
        "--session-id",
        dest="session_id",
        default=None,
        help="Optional session identifier to continue an existing session.",
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the legacy run parser kept for backward-compatible CLI execution."""

    parser = argparse.ArgumentParser(
        prog="python -m interfaces.cli",
        description="Run the local-first data_analyst agent on a local dataset.",
    )
    _add_run_arguments(parser)
    return parser


def build_command_parser() -> argparse.ArgumentParser:
    """Build the command-oriented parser for run/status/config operations."""

    parser = argparse.ArgumentParser(
        prog="python -m interfaces.cli",
        description="Operate the local-first product from the CLI.",
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Execute the data_analyst run flow.")
    _add_run_arguments(run_parser)

    status_parser = subparsers.add_parser("status", help="Check local readiness and provider health.")
    status_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Render the readiness report as JSON.",
    )

    config_parser = subparsers.add_parser("config", help="Show the effective local product configuration.")
    config_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Render the effective configuration as JSON.",
    )

    return parser


def build_default_runtime_coordinator(
    artifacts_root: str | Path = DEFAULT_ARTIFACTS_ROOT,
) -> RuntimeCoordinator:
    """Compose the default runtime used by the CLI."""

    return RuntimeCoordinator(
        dataset_preparer=LocalDatasetPreparer(),
        agent_registry=build_default_agent_registry(),
        artifacts_root=artifacts_root,
    )


def build_default_operational_service(
    artifacts_root: str | Path = DEFAULT_ARTIFACTS_ROOT,
) -> OperationalReadinessService:
    """Compose the default operational readiness service used by the CLI."""

    return build_default_operational_readiness_service(artifacts_root=artifacts_root)


def build_run_request(args: argparse.Namespace) -> RunRequest:
    """Translate CLI args into the core RunRequest contract."""

    try:
        return RunRequest(
            agent_id=args.agent_id,
            dataset_path=args.dataset_path,
            user_prompt=args.user_prompt,
            session_id=args.session_id,
        )
    except (TypeError, ValueError) as exc:
        raise RunError(
            code="invalid_request",
            message=str(exc),
            stage=ErrorStage.REQUEST_VALIDATION,
        ) from exc


def render_success(result, session_id: str) -> str:
    """Render a brief human-readable success response."""

    lines = [
        "Análisis completado",
        "",
        "Narrativa:",
        result.narrative,
    ]

    if result.findings:
        lines.extend(
            [
                "",
                "Hallazgos:",
                *[f"- {finding}" for finding in result.findings],
            ]
        )

    lines.extend(
        [
            "",
            f"Session ID: {session_id}",
            f"Run ID: {result.artifact_manifest.run_id}",
        ]
    )

    if result.artifact_manifest.response_path:
        lines.append(f"Response artifact: {result.artifact_manifest.response_path}")

    if result.artifact_manifest.table_paths:
        lines.extend(
            [
                "Table artifacts:",
                *[f"- {path}" for path in result.artifact_manifest.table_paths],
            ]
        )

    if result.artifact_manifest.chart_paths:
        lines.extend(
            [
                "Chart artifacts:",
                *[f"- {path}" for path in result.artifact_manifest.chart_paths],
            ]
        )

    return "\n".join(lines) + "\n"


def render_error(error: RunError) -> str:
    """Render a brief human-readable error response."""

    lines = [
        f"Error code: {error.code}",
        f"Stage: {error.stage.value}",
        f"Message: {error.message}",
    ]

    if error.details:
        lines.append("Details:")
        for key in sorted(error.details):
            lines.append(f"- {key}: {error.details[key]}")

    return "\n".join(lines) + "\n"


def render_status(report: ReadinessReport, *, json_output: bool = False) -> str:
    """Render operational status in human or machine-readable form."""

    if json_output:
        return json.dumps(_to_jsonable(report), indent=2, ensure_ascii=False) + "\n"

    app = report.application
    provider = report.provider
    lines = [
        f"System ready: {'yes' if report.ready else 'no'}",
        f"Status: {report.status.value}",
        "",
        "Application health:",
        f"- status: {app.status.value}",
        f"- default_agent_id: {app.default_agent_id}",
        f"- artifacts_root: {app.artifacts_root}",
    ]

    for check_name in sorted(app.checks):
        lines.append(f"- {check_name}: {'ok' if app.checks[check_name] else 'error'}")

    lines.extend(
        [
            "",
            "Provider health:",
            f"- status: {provider.status.value}",
            f"- proveedor: {provider.proveedor}",
            f"- endpoint: {provider.endpoint}",
            f"- binary_available: {'yes' if provider.binary_available else 'no'}",
            f"- reachable: {'yes' if provider.reachable else 'no'}",
            f"- model: {provider.model}",
            f"- model_available: {'yes' if provider.model_available else 'no'}",
        ]
    )

    if provider.binary_path:
        lines.append(f"- binary_path: {provider.binary_path}")
    if provider.version:
        lines.append(f"- version: {provider.version}")

    if report.issues:
        lines.extend(["", "Actionable issues:"])
        lines.extend(f"- {issue}" for issue in report.issues)

    return "\n".join(lines) + "\n"


def render_config(config, *, json_output: bool = False) -> str:
    """Render effective app config in human or machine-readable form."""

    if json_output:
        return json.dumps(_to_jsonable(config), indent=2, ensure_ascii=False) + "\n"

    lines = [
        "Effective config:",
        f"- default_agent_id: {config.default_agent_id}",
        f"- supported_dataset_formats: {', '.join(config.supported_dataset_formats)}",
        f"- proveedor_name: {config.proveedor_name}",
        f"- proveedor_endpoint: {config.proveedor_endpoint}",
        f"- required_model: {config.required_model}",
    ]
    return "\n".join(lines) + "\n"


def execute_cli(
    argv: list[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    runtime_coordinator: RuntimeCoordinator | None = None,
    operational_readiness_service: OperationalReadinessService | None = None,
) -> int:
    """Execute the CLI entrypoint and return a process exit code."""

    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    argv = list(sys.argv[1:] if argv is None else argv)

    if not argv:
        build_command_parser().print_help(stdout)
        return 2

    if argv[0] in _KNOWN_COMMANDS:
        args = build_command_parser().parse_args(argv)
        if args.command == "status":
            readiness_service = operational_readiness_service or build_default_operational_service()
            report = GetOperationalStatusUseCase(readiness_service).execute()
            stdout.write(render_status(report, json_output=args.json_output))
            return 0 if report.ready else 1
        if args.command == "config":
            readiness_service = operational_readiness_service or build_default_operational_service()
            config = GetAppConfigUseCase(readiness_service).execute()
            stdout.write(render_config(config, json_output=args.json_output))
            return 0
        return _execute_run(
            args,
            stdout=stdout,
            stderr=stderr,
            runtime_coordinator=runtime_coordinator,
        )

    args = build_parser().parse_args(argv)
    return _execute_run(
        args,
        stdout=stdout,
        stderr=stderr,
        runtime_coordinator=runtime_coordinator,
    )


def _execute_run(
    args: argparse.Namespace,
    *,
    stdout: TextIO,
    stderr: TextIO,
    runtime_coordinator: RuntimeCoordinator | None,
) -> int:
    coordinator = runtime_coordinator or build_default_runtime_coordinator()
    use_case = RunAnalysisUseCase(runtime=coordinator)

    try:
        request = build_run_request(args)
        result = use_case.execute(request)
        run_record = coordinator.tracker.get(result.artifact_manifest.run_id)
    except RunError as error:
        stderr.write(render_error(error))
        return 1

    stdout.write(render_success(result, session_id=run_record.session_id))
    return 0


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {key: _to_jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(item) for item in value]
    return value


def main(argv: list[str] | None = None) -> int:
    """Process entrypoint used by `python -m interfaces.cli`."""

    return execute_cli(argv)


__all__ = [
    "DEFAULT_ARTIFACTS_ROOT",
    "build_command_parser",
    "build_default_operational_service",
    "build_default_runtime_coordinator",
    "build_parser",
    "build_run_request",
    "execute_cli",
    "main",
    "render_config",
    "render_error",
    "render_status",
    "render_success",
]
