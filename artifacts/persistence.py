"""Filesystem persistence for run artifacts in the MVP."""

from __future__ import annotations

import json
from pathlib import Path
import re
import shutil

from application.contracts import AgentResult, ArtifactManifest, ErrorStage, RunError


_FILENAME_SANITIZER = re.compile(r"[^a-zA-Z0-9_.-]+")


def _slugify_filename(value: str, default: str) -> str:
    normalized = _FILENAME_SANITIZER.sub("_", value.strip()).strip("._")
    return normalized or default


class FilesystemArtifactPersister:
    """Persist minimal run outputs to the local filesystem."""

    def __call__(self, result: AgentResult, output_dir: str | Path) -> ArtifactManifest:
        if not isinstance(result, AgentResult):
            raise TypeError("result must be an AgentResult instance")

        run_id = result.artifact_manifest.run_id
        target_dir = Path(output_dir).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)

        response_path = self._write_response(result, target_dir)
        table_paths = self._write_tables(result, target_dir)
        chart_paths = self._copy_charts(result, target_dir)

        return ArtifactManifest(
            run_id=run_id,
            response_path=str(response_path),
            table_paths=[str(path) for path in table_paths],
            chart_paths=[str(path) for path in chart_paths],
        )

    def _write_response(self, result: AgentResult, output_dir: Path) -> Path:
        response_path = output_dir / "response.md"
        sections = [
            "# Narrative",
            "",
            result.narrative,
        ]

        if result.findings:
            sections.extend(
                [
                    "",
                    "## Findings",
                    "",
                    *[f"- {finding}" for finding in result.findings],
                ]
            )

        if result.recommendations:
            sections.extend(
                [
                    "",
                    "## Recommendations",
                    "",
                    *[f"- {recommendation}" for recommendation in result.recommendations],
                ]
            )

        response_path.write_text("\n".join(sections) + "\n", encoding="utf-8")
        return response_path

    def _write_tables(self, result: AgentResult, output_dir: Path) -> list[Path]:
        if not result.tables:
            return []

        tables_dir = output_dir / "tables"
        tables_dir.mkdir(parents=True, exist_ok=True)

        persisted_paths: list[Path] = []
        used_names: set[str] = set()
        for index, table in enumerate(result.tables, start=1):
            base_name = _slugify_filename(table.name, default=f"table_{index}")
            filename = f"{base_name}.json"
            suffix = 2
            while filename in used_names:
                filename = f"{base_name}_{suffix}.json"
                suffix += 1

            used_names.add(filename)
            table_path = tables_dir / filename
            table_path.write_text(
                json.dumps(table.rows, ensure_ascii=False, indent=2, default=str) + "\n",
                encoding="utf-8",
            )
            persisted_paths.append(table_path)

        return persisted_paths

    def _copy_charts(self, result: AgentResult, output_dir: Path) -> list[Path]:
        if not result.charts:
            return []

        charts_dir = output_dir / "charts"
        persisted_paths: list[Path] = []
        used_names: set[str] = set()

        for index, chart in enumerate(result.charts, start=1):
            if chart.path is None:
                continue

            source_path = Path(chart.path)
            if not source_path.exists() or not source_path.is_file():
                raise RunError(
                    code="artifact_chart_source_missing",
                    message="Chart source path does not exist or is not a file",
                    stage=ErrorStage.ARTIFACT_PERSISTENCE,
                    details={
                        "run_id": result.artifact_manifest.run_id,
                        "chart_name": chart.name,
                        "chart_path": chart.path,
                    },
                )

            charts_dir.mkdir(parents=True, exist_ok=True)
            extension = source_path.suffix or ".bin"
            base_name = _slugify_filename(chart.name, default=f"chart_{index}")
            filename = f"{base_name}{extension}"
            suffix = 2
            while filename in used_names:
                filename = f"{base_name}_{suffix}{extension}"
                suffix += 1

            used_names.add(filename)
            destination = charts_dir / filename
            shutil.copy2(source_path, destination)
            persisted_paths.append(destination)

        return persisted_paths
