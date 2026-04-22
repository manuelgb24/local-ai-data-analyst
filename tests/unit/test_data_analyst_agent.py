import pytest

from agents.data_analyst import DataAnalystAgent
from application import (
    AgentExecutionContext,
    DatasetColumn,
    DatasetProfile,
    ErrorStage,
    RunError,
    RunRequest,
)


class FakeLLMAdapter:
    def __init__(self, response: str = "Narrativa generada") -> None:
        self.response = response
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.response


class FakeDuckDBContext:
    def __init__(self, results: dict[str, list[tuple[object, ...]]]) -> None:
        self.results = results
        self.statements: list[str] = []

    def fetchall(self, sql: str) -> list[tuple[object, ...]]:
        self.statements.append(sql)
        if sql not in self.results:
            raise AssertionError(f"unexpected sql: {sql}")
        return self.results[sql]


class PatternDuckDBContext:
    def __init__(self) -> None:
        self.statements: list[str] = []

    def fetchall(self, sql: str) -> list[tuple[object, ...]]:
        self.statements.append(sql)
        if "GROUP BY" in sql and '"Branch"' in sql and '"Study_Hours_per_Day"' in sql:
            return [
                ("Civil", 177, 753.48, 4.26),
                ("ECE", 161, 655.46, 4.07),
            ]
        if "CORR" in sql and '"Sleep_Hours"' in sql and '"Gym_Hours_per_Week"' in sql:
            return [(0.0147, 6.53, 7.31)]
        if "COUNT(*) AS row_count" in sql and "GROUP BY" in sql:
            return [("Civil", 177), ("IT", 176)]
        if "AVG(CAST" in sql:
            return [
                ("Study_Hours_per_Day", 1000, 4.04, 0.5, 8.05),
                ("Sleep_Hours", 1000, 6.53, 3.0, 10.0),
                ("Gym_Hours_per_Week", 1000, 7.31, 0.0, 20.0),
            ]
        if sql.startswith('SELECT * FROM "dataset_run_123"'):
            return [
                (23, "ECE", 4.14, 6.84, 2.67),
                (20, "Civil", 5.97, 5.52, 15.61),
            ]
        raise AssertionError(f"unexpected sql: {sql}")


def build_request() -> RunRequest:
    return RunRequest(
        agent_id="data_analyst",
        dataset_path="DatasetV1/demo_business_metrics.csv",
        user_prompt="Resume los hallazgos principales",
    )


def build_context(duckdb_context: object, schema: list[DatasetColumn]) -> AgentExecutionContext:
    return AgentExecutionContext(
        run_id="run-123",
        session_id="session-123",
        dataset_profile=DatasetProfile(
            source_path="DatasetV1/demo_business_metrics.csv",
            format="csv",
            table_name="dataset_run_123",
            schema=schema,
            row_count=6,
        ),
        duckdb_context=duckdb_context,
        output_dir="artifacts/runs/run-123",
    )


def test_data_analyst_agent_builds_result_with_preview_and_numeric_summary() -> None:
    preview_sql = 'SELECT * FROM "dataset_run_123" LIMIT 5'
    summary_sql = "\nUNION ALL\n".join(
        [
            "\n".join(
                [
                    "SELECT 'store' AS column_name,",
                    'COUNT("store") AS non_null_count,',
                    'AVG(CAST("store" AS DOUBLE)) AS avg_value,',
                    'MIN(CAST("store" AS DOUBLE)) AS min_value,',
                    'MAX(CAST("store" AS DOUBLE)) AS max_value',
                    'FROM "dataset_run_123"',
                ]
            ),
            "\n".join(
                [
                    "SELECT 'weekly_sales' AS column_name,",
                    'COUNT("weekly_sales") AS non_null_count,',
                    'AVG(CAST("weekly_sales" AS DOUBLE)) AS avg_value,',
                    'MIN(CAST("weekly_sales" AS DOUBLE)) AS min_value,',
                    'MAX(CAST("weekly_sales" AS DOUBLE)) AS max_value',
                    'FROM "dataset_run_123"',
                ]
            ),
            "\n".join(
                [
                    "SELECT 'temperature' AS column_name,",
                    'COUNT("temperature") AS non_null_count,',
                    'AVG(CAST("temperature" AS DOUBLE)) AS avg_value,',
                    'MIN(CAST("temperature" AS DOUBLE)) AS min_value,',
                    'MAX(CAST("temperature" AS DOUBLE)) AS max_value',
                    'FROM "dataset_run_123"',
                ]
            ),
        ]
    )
    llm = FakeLLMAdapter(response="Narrativa breve")
    agent = DataAnalystAgent(llm_adapter=llm)
    context = build_context(
        duckdb_context=FakeDuckDBContext(
            {
                preview_sql: [(1, 100.0, 25.0), (2, 150.0, 27.5)],
                summary_sql: [
                    ("store", 6, 1.5, 1.0, 2.0),
                    ("weekly_sales", 6, 125.0, 100.0, 150.0),
                    ("temperature", 6, 26.25, 25.0, 27.5),
                ],
            }
        ),
        schema=[
            DatasetColumn(name="store", type="BIGINT"),
            DatasetColumn(name="weekly_sales", type="DOUBLE"),
            DatasetColumn(name="temperature", type="DOUBLE"),
        ],
    )

    result = agent(build_request(), context)

    assert result.narrative == "Narrativa breve"
    assert result.findings == [
        "Dataset has 6 rows and 3 columns.",
        "Preview query returned 2 rows.",
        "Column store: count=6, avg=1.5, min=1.0, max=2.0.",
        "Column weekly_sales: count=6, avg=125.0, min=100.0, max=150.0.",
        "Column temperature: count=6, avg=26.25, min=25.0, max=27.5.",
    ]
    assert [entry.statement for entry in result.sql_trace] == [preview_sql, summary_sql]
    assert [entry.rows_returned for entry in result.sql_trace] == [2, 3]
    assert [table.name for table in result.tables] == ["preview", "numeric_summary"]
    assert result.tables[0].rows == [
        {"store": 1, "weekly_sales": 100.0, "temperature": 25.0},
        {"store": 2, "weekly_sales": 150.0, "temperature": 27.5},
    ]
    assert [row["column_name"] for row in result.tables[1].rows] == [
        "store",
        "weekly_sales",
        "temperature",
    ]
    assert result.charts == []
    assert result.artifact_manifest.run_id == "run-123"
    assert result.artifact_manifest.table_paths == []
    assert llm.prompts and "Resume los hallazgos principales" in llm.prompts[0]


def test_data_analyst_agent_builds_grouped_study_ranking_and_embedded_chart() -> None:
    llm = FakeLLMAdapter(response="El patrón confirma que Civil lidera.")
    agent = DataAnalystAgent(llm_adapter=llm)
    context = build_context(
        duckdb_context=PatternDuckDBContext(),
        schema=[
            DatasetColumn(name="Age", type="BIGINT"),
            DatasetColumn(name="Branch", type="VARCHAR"),
            DatasetColumn(name="Study_Hours_per_Day", type="DOUBLE"),
            DatasetColumn(name="Sleep_Hours", type="DOUBLE"),
            DatasetColumn(name="Gym_Hours_per_Week", type="DOUBLE"),
        ],
    )
    request = RunRequest(
        agent_id="data_analyst",
        dataset_path="DatasetV1/demo_business_metrics.csv",
        user_prompt="dime cual es la carrera (branch) en la que mas se estudia",
        session_id="chat-123",
        conversation_context=[{"role": "user", "content": "Estamos analizando el dataset de estudiantes."}],
    )

    result = agent(request, context)

    ranking = next(table for table in result.tables if table.name == "ranking_Branch_by_Study_Hours_per_Day")
    assert ranking.rows[0] == {
        "Branch": "Civil",
        "row_count": 177,
        "total_Study_Hours_per_Day": 753.48,
        "avg_Study_Hours_per_Day": 4.26,
        "rank": 1,
    }
    assert result.charts
    assert result.charts[0].chart_type == "bar"
    assert result.charts[0].x_key == "Branch"
    assert result.charts[0].y_key == "avg_Study_Hours_per_Day"
    assert result.charts[0].data[0]["Branch"] == "Civil"
    assert any("Civil" in finding and "Study_Hours_per_Day" in finding for finding in result.findings)
    assert not result.narrative.lower().startswith(("conclusión:", "conclusion:"))
    assert "Civil" in result.narrative
    assert '"conversation_context"' in llm.prompts[0]
    assert "Dataset has" not in llm.prompts[0]
    assert "Preview query returned" not in llm.prompts[0]
    assert '"preview_rows": []' in llm.prompts[0]
    assert '"numeric_summary": []' in llm.prompts[0]


def test_data_analyst_agent_strips_repetitive_section_headings_from_narrative() -> None:
    llm = FakeLLMAdapter(
        response=(
            "Conclusión: Civil lidera por horas de estudio.\n\n"
            "Contexto: La tabla derivada compara las carreras.\n\n"
            "Nota: No hace falta revisar rutas técnicas."
        )
    )
    agent = DataAnalystAgent(llm_adapter=llm)
    context = build_context(
        duckdb_context=PatternDuckDBContext(),
        schema=[
            DatasetColumn(name="Branch", type="VARCHAR"),
            DatasetColumn(name="Study_Hours_per_Day", type="DOUBLE"),
        ],
    )
    request = RunRequest(
        agent_id="data_analyst",
        dataset_path="DatasetV1/demo_business_metrics.csv",
        user_prompt="dime cual es la carrera branch en la que mas se estudia",
    )

    result = agent(request, context)

    normalized = result.narrative.lower()
    assert "conclusión:" not in normalized
    assert "conclusion:" not in normalized
    assert "contexto:" not in normalized
    assert "nota:" not in normalized
    assert "Civil" in result.narrative


def test_data_analyst_agent_builds_correlation_for_two_numeric_columns() -> None:
    llm = FakeLLMAdapter(response="La relación es prácticamente nula.")
    agent = DataAnalystAgent(llm_adapter=llm)
    context = build_context(
        duckdb_context=PatternDuckDBContext(),
        schema=[
            DatasetColumn(name="Age", type="BIGINT"),
            DatasetColumn(name="Branch", type="VARCHAR"),
            DatasetColumn(name="Study_Hours_per_Day", type="DOUBLE"),
            DatasetColumn(name="Sleep_Hours", type="DOUBLE"),
            DatasetColumn(name="Gym_Hours_per_Week", type="DOUBLE"),
        ],
    )
    request = RunRequest(
        agent_id="data_analyst",
        dataset_path="DatasetV1/demo_business_metrics.csv",
        user_prompt="los alumnos que mas duermen son los que mas horas van al gym?",
    )

    result = agent(request, context)

    correlation = next(table for table in result.tables if table.name == "correlation_Sleep_Hours_Gym_Hours_per_Week")
    assert correlation.rows == [
        {
            "left_column": "Sleep_Hours",
            "right_column": "Gym_Hours_per_Week",
            "correlation": 0.0147,
            "avg_Sleep_Hours": 6.53,
            "avg_Gym_Hours_per_Week": 7.31,
        }
    ]
    assert any("correlación" in finding.lower() and "0.0147" in finding for finding in result.findings)


def test_data_analyst_agent_builds_category_counts_when_only_dimension_is_requested() -> None:
    llm = FakeLLMAdapter(response="Civil es la categoría con más alumnos.")
    agent = DataAnalystAgent(llm_adapter=llm)
    context = build_context(
        duckdb_context=PatternDuckDBContext(),
        schema=[
            DatasetColumn(name="Branch", type="VARCHAR"),
            DatasetColumn(name="Study_Hours_per_Day", type="DOUBLE"),
        ],
    )
    request = RunRequest(
        agent_id="data_analyst",
        dataset_path="DatasetV1/demo_business_metrics.csv",
        user_prompt="cuantos alumnos hay por carrera branch?",
    )

    result = agent(request, context)

    counts = next(table for table in result.tables if table.name == "top_Branch_counts")
    assert counts.rows == [
        {"Branch": "Civil", "row_count": 177, "rank": 1},
        {"Branch": "IT", "row_count": 176, "rank": 2},
    ]
    assert result.charts[0].name == "top_Branch_counts"
    assert result.charts[0].y_key == "row_count"


def test_data_analyst_agent_handles_datasets_without_numeric_columns() -> None:
    preview_sql = 'SELECT * FROM "dataset_run_123" LIMIT 5'
    llm = FakeLLMAdapter()
    agent = DataAnalystAgent(llm_adapter=llm)
    context = build_context(
        duckdb_context=FakeDuckDBContext(
            {
                preview_sql: [("A", "North"), ("B", "South")],
            }
        ),
        schema=[
            DatasetColumn(name="store_name", type="VARCHAR"),
            DatasetColumn(name="region", type="VARCHAR"),
        ],
    )

    result = agent(build_request(), context)

    assert len(result.sql_trace) == 1
    assert result.sql_trace[0].statement == preview_sql
    assert [table.name for table in result.tables] == ["preview"]
    assert result.findings == [
        "Dataset has 6 rows and 2 columns.",
        "Preview query returned 2 rows.",
        "Dataset has no numeric columns available for aggregate summary.",
    ]
    assert '"numeric_summary": []' in llm.prompts[0]


def test_data_analyst_agent_maps_unexpected_sql_errors_to_run_error() -> None:
    class ExplodingDuckDBContext:
        def fetchall(self, sql: str) -> list[tuple[object, ...]]:
            raise RuntimeError("boom")

    agent = DataAnalystAgent(llm_adapter=FakeLLMAdapter())
    context = build_context(
        duckdb_context=ExplodingDuckDBContext(),
        schema=[DatasetColumn(name="sales", type="DOUBLE")],
    )

    with pytest.raises(RunError) as exc_info:
        agent(build_request(), context)

    assert exc_info.value.code == "agent_query_failed"
    assert exc_info.value.stage is ErrorStage.AGENT_EXECUTION
    assert exc_info.value.details == {
        "run_id": "run-123",
        "table_name": "dataset_run_123",
        'statement': 'SELECT * FROM "dataset_run_123" LIMIT 5',
        "purpose": "preview_dataset",
        "error_type": "RuntimeError",
        "error_message": "boom",
    }


def test_data_analyst_agent_propagates_run_error_from_llm_adapter() -> None:
    class FailingLLMAdapter:
        def generate(self, prompt: str) -> str:
            raise RunError(
                code="llm_provider_unavailable",
                message="Ollama no disponible",
                stage=ErrorStage.AGENT_EXECUTION,
            )

    preview_sql = 'SELECT * FROM "dataset_run_123" LIMIT 5'
    summary_sql = "\n".join(
        [
            "SELECT 'sales' AS column_name,",
            'COUNT("sales") AS non_null_count,',
            'AVG(CAST("sales" AS DOUBLE)) AS avg_value,',
            'MIN(CAST("sales" AS DOUBLE)) AS min_value,',
            'MAX(CAST("sales" AS DOUBLE)) AS max_value',
            'FROM "dataset_run_123"',
        ]
    )
    agent = DataAnalystAgent(llm_adapter=FailingLLMAdapter())
    context = build_context(
        duckdb_context=FakeDuckDBContext(
            {
                preview_sql: [(100.0,)],
                summary_sql: [("sales", 1, 100.0, 100.0, 100.0)],
            }
        ),
        schema=[DatasetColumn(name="sales", type="DOUBLE")],
    )

    with pytest.raises(RunError) as exc_info:
        agent(build_request(), context)

    assert exc_info.value.code == "llm_provider_unavailable"
    assert exc_info.value.message == "Ollama no disponible"
