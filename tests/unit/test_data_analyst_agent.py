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


def build_request() -> RunRequest:
    return RunRequest(
        agent_id="data_analyst",
        dataset_path="DatasetV1/Walmart_Sales.csv",
        user_prompt="Resume los hallazgos principales",
    )


def build_context(duckdb_context: object, schema: list[DatasetColumn]) -> AgentExecutionContext:
    return AgentExecutionContext(
        run_id="run-123",
        session_id="session-123",
        dataset_profile=DatasetProfile(
            source_path="DatasetV1/Walmart_Sales.csv",
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
