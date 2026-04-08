"""Real `data_analyst` agent implementation for the MVP."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol

from adapters.duckdb_adapter import quote_identifier
from application.contracts import (
    AgentExecutionContext,
    AgentResult,
    ArtifactManifest,
    ChartReference,
    ErrorStage,
    RunError,
    RunRequest,
    SqlTraceEntry,
    SqlTraceStatus,
    TableResult,
)


class LLMAdapter(Protocol):
    def generate(self, prompt: str) -> str: ...


_NUMERIC_TYPE_MARKERS = (
    "TINYINT",
    "SMALLINT",
    "INTEGER",
    "BIGINT",
    "HUGEINT",
    "UTINYINT",
    "USMALLINT",
    "UINTEGER",
    "UBIGINT",
    "UHUGEINT",
    "FLOAT",
    "REAL",
    "DOUBLE",
    "DECIMAL",
    "NUMERIC",
)


@dataclass(slots=True)
class DataAnalystAgent:
    """Single real MVP agent that summarizes a prepared dataset."""

    llm_adapter: LLMAdapter

    def __call__(self, request: RunRequest, context: AgentExecutionContext) -> AgentResult:
        preview_statement = self._build_preview_statement(context.dataset_profile.table_name)
        preview_rows, preview_trace = self._run_query(
            context=context,
            statement=preview_statement,
            purpose="preview_dataset",
        )

        preview_table = TableResult(
            name="preview",
            rows=self._rows_to_dicts(context.dataset_profile.schema, preview_rows),
        )

        numeric_columns = self._numeric_columns(context)
        summary_table: TableResult | None = None
        sql_trace = [preview_trace]

        if numeric_columns:
            summary_statement = self._build_summary_statement(context.dataset_profile.table_name, numeric_columns)
            summary_rows, summary_trace = self._run_query(
                context=context,
                statement=summary_statement,
                purpose="summarize_numeric_columns",
            )
            sql_trace.append(summary_trace)
            summary_table = TableResult(
                name="numeric_summary",
                rows=self._summary_rows_to_dicts(summary_rows),
            )

        findings = self._build_findings(context, preview_table, summary_table)
        prompt = self._build_prompt(request, context, preview_table, summary_table, findings)
        narrative = self.llm_adapter.generate(prompt)

        tables = [preview_table]
        if summary_table is not None:
            tables.append(summary_table)

        return AgentResult(
            narrative=narrative,
            findings=findings,
            sql_trace=sql_trace,
            tables=tables,
            charts=[],
            artifact_manifest=ArtifactManifest(
                run_id=context.run_id,
                table_paths=[],
                chart_paths=[],
            ),
        )

    def _build_preview_statement(self, table_name: str) -> str:
        return f"SELECT * FROM {quote_identifier(table_name)} LIMIT 5"

    def _build_summary_statement(self, table_name: str, numeric_columns: list[str]) -> str:
        summary_parts = []
        for column_name in numeric_columns[:3]:
            quoted_column = quote_identifier(column_name)
            summary_parts.append(
                "\n".join(
                    [
                        f"SELECT '{column_name}' AS column_name,",
                        f"COUNT({quoted_column}) AS non_null_count,",
                        f"AVG(CAST({quoted_column} AS DOUBLE)) AS avg_value,",
                        f"MIN(CAST({quoted_column} AS DOUBLE)) AS min_value,",
                        f"MAX(CAST({quoted_column} AS DOUBLE)) AS max_value",
                        f"FROM {quote_identifier(table_name)}",
                    ]
                )
            )
        return "\nUNION ALL\n".join(summary_parts)

    def _numeric_columns(self, context: AgentExecutionContext) -> list[str]:
        return [
            column.name
            for column in context.dataset_profile.schema
            if any(marker in column.type.upper() for marker in _NUMERIC_TYPE_MARKERS)
        ]

    def _run_query(
        self,
        context: AgentExecutionContext,
        statement: str,
        purpose: str,
    ) -> tuple[list[tuple[object, ...]], SqlTraceEntry]:
        try:
            rows = context.duckdb_context.fetchall(statement)
        except RunError:
            raise
        except Exception as exc:
            raise RunError(
                code="agent_query_failed",
                message="data_analyst failed while querying DuckDB",
                stage=ErrorStage.AGENT_EXECUTION,
                details={
                    "run_id": context.run_id,
                    "table_name": context.dataset_profile.table_name,
                    "statement": statement,
                    "purpose": purpose,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                },
            ) from exc

        trace = SqlTraceEntry(
            statement=statement,
            status=SqlTraceStatus.OK,
            purpose=purpose,
            rows_returned=len(rows),
        )
        return rows, trace

    def _rows_to_dicts(self, schema: list[Any], rows: list[tuple[object, ...]]) -> list[dict[str, Any]]:
        column_names = [column.name for column in schema]
        return [
            {
                column_name: row[index] if index < len(row) else None
                for index, column_name in enumerate(column_names)
            }
            for row in rows
        ]

    def _summary_rows_to_dicts(self, rows: list[tuple[object, ...]]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for column_name, non_null_count, avg_value, min_value, max_value in rows:
            results.append(
                {
                    "column_name": column_name,
                    "non_null_count": non_null_count,
                    "avg_value": avg_value,
                    "min_value": min_value,
                    "max_value": max_value,
                }
            )
        return results

    def _build_findings(
        self,
        context: AgentExecutionContext,
        preview_table: TableResult,
        summary_table: TableResult | None,
    ) -> list[str]:
        findings = [
            (
                f"Dataset has {context.dataset_profile.row_count} rows and "
                f"{len(context.dataset_profile.schema)} columns."
            ),
            f"Preview query returned {len(preview_table.rows)} rows.",
        ]

        if summary_table is None:
            findings.append("Dataset has no numeric columns available for aggregate summary.")
            return findings

        for row in summary_table.rows:
            findings.append(
                "Column {column_name}: count={non_null_count}, avg={avg_value}, min={min_value}, max={max_value}.".format(
                    **row
                )
            )
        return findings

    def _build_prompt(
        self,
        request: RunRequest,
        context: AgentExecutionContext,
        preview_table: TableResult,
        summary_table: TableResult | None,
        findings: list[str],
    ) -> str:
        prompt_payload = {
            "user_prompt": request.user_prompt,
            "run_id": context.run_id,
            "dataset_profile": {
                "source_path": context.dataset_profile.source_path,
                "format": context.dataset_profile.format,
                "table_name": context.dataset_profile.table_name,
                "row_count": context.dataset_profile.row_count,
                "schema": [
                    {"name": column.name, "type": column.type}
                    for column in context.dataset_profile.schema
                ],
            },
            "preview_rows": preview_table.rows,
            "numeric_summary": [] if summary_table is None else summary_table.rows,
            "deterministic_findings": findings,
        }
        return "\n".join(
            [
                "You are the MVP local-first data_analyst agent.",
                "Write a brief narrative in Spanish using only the provided dataset context.",
                "Do not invent columns, metrics, trends, charts, or file outputs.",
                "Mention uncertainty explicitly if the available context is limited.",
                json.dumps(prompt_payload, ensure_ascii=False, default=str, indent=2),
            ]
        )
