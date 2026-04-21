"""Real `data_analyst` agent implementation for the MVP."""

from __future__ import annotations

import json
from dataclasses import dataclass
import re
from typing import Any, Protocol
import unicodedata

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

_DIMENSION_ALIASES = {
    "branch": ("branch", "carrera", "grado", "especialidad"),
    "store": ("store", "tienda"),
    "region": ("region", "zona"),
    "department": ("department", "departamento"),
    "category": ("category", "categoria", "categoría", "tipo"),
}

_METRIC_ALIASES = {
    "study": ("study", "estudia", "estudian", "estudio", "estudiar", "horasdeestudio"),
    "sleep": ("sleep", "duerme", "duermen", "dormir", "sueno", "sueño"),
    "gym": ("gym", "gimnasio", "ejercicio", "entreno"),
    "sales": ("sales", "venta", "ventas", "vendido", "venden"),
    "mark": ("mark", "marks", "nota", "notas"),
    "cgpa": ("cgpa", "gpa"),
    "attendance": ("attendance", "asistencia"),
    "stress": ("stress", "estres", "estrés"),
}

_RELATION_TERMS = ("correl", "relacion", "relación", "asoci", "sonlosque", "compar")
_REPETITIVE_SECTION_PREFIX = re.compile(r"(?im)^\s*(conclusi[oó]n|contexto|nota)\s*:\s*")


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
        tables = [preview_table]
        if summary_table is not None:
            tables.append(summary_table)

        tool_tables, tool_traces, tool_findings, charts, primary_answer = self._run_prompt_tools(
            request=request,
            context=context,
        )
        tables.extend(tool_tables)
        sql_trace.extend(tool_traces)
        findings.extend(tool_findings)

        prompt = self._build_prompt(
            request,
            context,
            preview_table,
            summary_table,
            tool_findings,
            analysis_tables=tool_tables,
            charts=charts,
        )
        narrative = self._compose_narrative(
            deterministic_answer=primary_answer,
            llm_narrative=self.llm_adapter.generate(prompt),
        )

        return AgentResult(
            narrative=narrative,
            findings=findings,
            sql_trace=sql_trace,
            tables=tables,
            charts=charts,
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

    def _run_prompt_tools(
        self,
        *,
        request: RunRequest,
        context: AgentExecutionContext,
    ) -> tuple[list[TableResult], list[SqlTraceEntry], list[str], list[ChartReference], str | None]:
        dimension = self._resolve_dimension_column(request, context)
        metrics = self._resolve_metric_columns(request, context)
        tables: list[TableResult] = []
        traces: list[SqlTraceEntry] = []
        findings: list[str] = []
        charts: list[ChartReference] = []
        primary_answer: str | None = None

        if dimension is not None and metrics:
            metric = metrics[0]
            statement = self._build_grouped_ranking_statement(
                table_name=context.dataset_profile.table_name,
                dimension_column=dimension,
                metric_column=metric,
            )
            rows, trace = self._run_query(
                context=context,
                statement=statement,
                purpose="rank_dimension_by_metric",
            )
            traces.append(trace)
            table_rows = self._grouped_ranking_rows_to_dicts(dimension, metric, rows)
            table = TableResult(name=f"ranking_{dimension}_by_{metric}", rows=table_rows)
            tables.append(table)

            if table_rows:
                top = table_rows[0]
                total_key = f"total_{metric}"
                avg_key = f"avg_{metric}"
                primary_answer = (
                    f"{top[dimension]} lidera en {metric}: media {top[avg_key]} y total {top[total_key]} "
                    f"sobre {top['row_count']} filas."
                )
                findings.append(
                    f"{dimension} con mayor promedio de {metric}: {top[dimension]} "
                    f"(avg={top[avg_key]}, total={top[total_key]}, filas={top['row_count']})."
                )
                charts.append(
                    ChartReference(
                        name=table.name,
                        chart_type="bar",
                        title=f"{metric} por {dimension}",
                        x_key=dimension,
                        y_key=avg_key,
                        data=table_rows,
                    )
                )

        elif dimension is not None:
            statement = self._build_category_count_statement(
                table_name=context.dataset_profile.table_name,
                dimension_column=dimension,
            )
            rows, trace = self._run_query(
                context=context,
                statement=statement,
                purpose="count_dimension_categories",
            )
            traces.append(trace)
            table_rows = self._category_count_rows_to_dicts(dimension, rows)
            table = TableResult(name=f"top_{dimension}_counts", rows=table_rows)
            tables.append(table)
            if table_rows:
                top = table_rows[0]
                primary_answer = f"{top[dimension]} es la categoría más frecuente de {dimension}, con {top['row_count']} filas."
                findings.append(
                    f"{dimension} más frecuente: {top[dimension]} (filas={top['row_count']})."
                )
                charts.append(
                    ChartReference(
                        name=table.name,
                        chart_type="bar",
                        title=f"Conteo por {dimension}",
                        x_key=dimension,
                        y_key="row_count",
                        data=table_rows,
                    )
                )

        elif len(metrics) >= 2 and self._looks_like_relation_prompt(request.user_prompt):
            left, right = metrics[:2]
            statement = self._build_correlation_statement(
                table_name=context.dataset_profile.table_name,
                left_column=left,
                right_column=right,
            )
            rows, trace = self._run_query(
                context=context,
                statement=statement,
                purpose="correlate_numeric_columns",
            )
            traces.append(trace)
            table_rows = self._correlation_rows_to_dicts(left, right, rows)
            table = TableResult(name=f"correlation_{left}_{right}", rows=table_rows)
            tables.append(table)
            if table_rows:
                correlation = table_rows[0]["correlation"]
                primary_answer = (
                    f"La correlación entre {left} y {right} es {correlation}; "
                    "en estos datos no sugiere una relación lineal fuerte."
                )
                findings.append(
                    f"Correlación {left} vs {right}: {correlation}."
                )

        return tables, traces, findings, charts, primary_answer

    def _build_grouped_ranking_statement(
        self,
        *,
        table_name: str,
        dimension_column: str,
        metric_column: str,
    ) -> str:
        quoted_dimension = quote_identifier(dimension_column)
        quoted_metric = quote_identifier(metric_column)
        return "\n".join(
            [
                f"SELECT {quoted_dimension} AS {quoted_dimension},",
                "COUNT(*) AS row_count,",
                f"ROUND(SUM(CAST({quoted_metric} AS DOUBLE)), 4) AS total_metric,",
                f"ROUND(AVG(CAST({quoted_metric} AS DOUBLE)), 4) AS avg_metric",
                f"FROM {quote_identifier(table_name)}",
                f"WHERE {quoted_dimension} IS NOT NULL AND {quoted_metric} IS NOT NULL",
                f"GROUP BY {quoted_dimension}",
                "ORDER BY avg_metric DESC, total_metric DESC, row_count DESC",
                "LIMIT 10",
            ]
        )

    def _build_category_count_statement(self, *, table_name: str, dimension_column: str) -> str:
        quoted_dimension = quote_identifier(dimension_column)
        return "\n".join(
            [
                f"SELECT {quoted_dimension} AS {quoted_dimension},",
                "COUNT(*) AS row_count",
                f"FROM {quote_identifier(table_name)}",
                f"WHERE {quoted_dimension} IS NOT NULL",
                f"GROUP BY {quoted_dimension}",
                "ORDER BY row_count DESC",
                "LIMIT 10",
            ]
        )

    def _build_correlation_statement(
        self,
        *,
        table_name: str,
        left_column: str,
        right_column: str,
    ) -> str:
        quoted_left = quote_identifier(left_column)
        quoted_right = quote_identifier(right_column)
        return "\n".join(
            [
                f"SELECT ROUND(CORR(CAST({quoted_left} AS DOUBLE), CAST({quoted_right} AS DOUBLE)), 4) AS correlation,",
                f"ROUND(AVG(CAST({quoted_left} AS DOUBLE)), 4) AS avg_left,",
                f"ROUND(AVG(CAST({quoted_right} AS DOUBLE)), 4) AS avg_right",
                f"FROM {quote_identifier(table_name)}",
                f"WHERE {quoted_left} IS NOT NULL AND {quoted_right} IS NOT NULL",
            ]
        )

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

    def _grouped_ranking_rows_to_dicts(
        self,
        dimension_column: str,
        metric_column: str,
        rows: list[tuple[object, ...]],
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for rank, (dimension_value, row_count, total_value, avg_value) in enumerate(rows, start=1):
            results.append(
                {
                    dimension_column: dimension_value,
                    "row_count": row_count,
                    f"total_{metric_column}": total_value,
                    f"avg_{metric_column}": avg_value,
                    "rank": rank,
                }
            )
        return results

    def _correlation_rows_to_dicts(
        self,
        left_column: str,
        right_column: str,
        rows: list[tuple[object, ...]],
    ) -> list[dict[str, Any]]:
        if not rows:
            return []
        correlation, avg_left, avg_right = rows[0]
        return [
            {
                "left_column": left_column,
                "right_column": right_column,
                "correlation": correlation,
                f"avg_{left_column}": avg_left,
                f"avg_{right_column}": avg_right,
            }
        ]

    def _category_count_rows_to_dicts(
        self,
        dimension_column: str,
        rows: list[tuple[object, ...]],
    ) -> list[dict[str, Any]]:
        return [
            {
                dimension_column: dimension_value,
                "row_count": row_count,
                "rank": rank,
            }
            for rank, (dimension_value, row_count) in enumerate(rows, start=1)
        ]

    def _resolve_dimension_column(self, request: RunRequest, context: AgentExecutionContext) -> str | None:
        prompt = self._normalize_text(request.user_prompt)
        scored: list[tuple[int, str]] = []
        for column in context.dataset_profile.schema:
            column_key = self._normalize_text(column.name)
            score = 0
            if column_key and column_key in prompt:
                score += 10
            for alias_key, aliases in _DIMENSION_ALIASES.items():
                if alias_key in column_key and any(self._normalize_text(alias) in prompt for alias in aliases):
                    score += 8
            if score > 0 and "VARCHAR" in column.type.upper():
                score += 1
            if score > 0:
                scored.append((score, column.name))
        if not scored:
            return None
        return sorted(scored, key=lambda item: item[0], reverse=True)[0][1]

    def _resolve_metric_columns(self, request: RunRequest, context: AgentExecutionContext) -> list[str]:
        prompt = self._normalize_text(request.user_prompt)
        scored: list[tuple[int, int, str]] = []
        numeric_columns = self._numeric_columns(context)
        for index, column_name in enumerate(numeric_columns):
            column_key = self._normalize_text(column_name)
            score = 0
            if column_key and column_key in prompt:
                score += 10
            for alias_key, aliases in _METRIC_ALIASES.items():
                if alias_key in column_key and any(self._normalize_text(alias) in prompt for alias in aliases):
                    score += 8
            if score > 0:
                scored.append((score, -index, column_name))
        return [column for _, _, column in sorted(scored, reverse=True)]

    def _looks_like_relation_prompt(self, prompt: str) -> bool:
        normalized = self._normalize_text(prompt)
        return any(self._normalize_text(term) in normalized for term in _RELATION_TERMS)

    def _normalize_text(self, value: str) -> str:
        decomposed = unicodedata.normalize("NFKD", value.lower())
        without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
        return re.sub(r"[^a-z0-9]+", "", without_accents)

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
        analysis_tables: list[TableResult] | None = None,
        charts: list[ChartReference] | None = None,
    ) -> str:
        has_analysis_tables = bool(analysis_tables)
        prompt_payload = {
            "user_prompt": request.user_prompt,
            "conversation_context": request.conversation_context or [],
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
            "preview_rows": [] if has_analysis_tables else preview_table.rows,
            "numeric_summary": [] if has_analysis_tables or summary_table is None else summary_table.rows,
            "analysis_tables": [] if analysis_tables is None else [
                {"name": table.name, "rows": table.rows} for table in analysis_tables
            ],
            "charts": [] if charts is None else [
                {
                    "name": chart.name,
                    "chart_type": chart.chart_type,
                    "title": chart.title,
                    "x_key": chart.x_key,
                    "y_key": chart.y_key,
                    "data": chart.data,
                }
                for chart in charts
            ],
            "deterministic_findings": findings,
        }
        return "\n".join(
            [
                "Eres data_analyst, un analista de datos local-first.",
                "Responde en español con tono claro, directo y profesional.",
                "Responde como en un chat normal: una respuesta natural, breve y útil.",
                "No uses secciones ni encabezados como Conclusión, Contexto o Nota salvo que el usuario lo pida.",
                "Integra la información importante dentro de la propia respuesta.",
                "No recites metadatos técnicos como número de filas/columnas, preview rows o summaries numéricos salvo que el usuario los pida.",
                "Cuando analysis_tables o deterministic_findings respondan la pregunta, usa esos datos para contestar de forma específica.",
                "No digas que no es posible determinar algo si una tabla derivada lo responde.",
                "Do not invent columns, metrics, trends, charts, or file outputs.",
                "Do not mention artifact paths, SQL traces, JSON files, or exported files.",
                "Mention uncertainty explicitly only if the available context is truly limited.",
                json.dumps(prompt_payload, ensure_ascii=False, default=str, indent=2),
            ]
        )

    def _compose_narrative(self, deterministic_answer: str | None, llm_narrative: str) -> str:
        llm_narrative = self._clean_narrative(llm_narrative)
        if deterministic_answer is None:
            return llm_narrative
        deterministic_answer = self._clean_narrative(deterministic_answer)
        if not llm_narrative:
            return deterministic_answer
        if llm_narrative.lower().startswith(deterministic_answer.lower()):
            return llm_narrative
        return f"{deterministic_answer}\n\n{llm_narrative}"

    def _clean_narrative(self, value: str) -> str:
        cleaned = _REPETITIVE_SECTION_PREFIX.sub("", value.strip())
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()
