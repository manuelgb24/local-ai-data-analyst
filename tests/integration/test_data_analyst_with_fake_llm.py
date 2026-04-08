from pathlib import Path

from agents.data_analyst import DataAnalystAgent
from application import AgentExecutionContext, RunRequest
from data import LocalDatasetPreparer


class FakeLLMAdapter:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return "Narrativa integrada"


def test_data_analyst_agent_integrates_with_prepared_duckdb_dataset(repo_tmp_path: Path) -> None:
    dataset_path = repo_tmp_path / "sales.csv"
    dataset_path.write_text(
        "\n".join(
            [
                "store,region,weekly_sales,temperature",
                "1,North,100.0,25.0",
                "2,South,150.0,27.5",
                "3,North,90.0,24.0",
            ]
        ),
        encoding="utf-8",
    )

    request = RunRequest(
        agent_id="data_analyst",
        dataset_path=str(dataset_path),
        user_prompt="Resume ventas y temperatura",
    )
    prepared = LocalDatasetPreparer()(request, "run-integration")
    llm = FakeLLMAdapter()
    agent = DataAnalystAgent(llm_adapter=llm)

    try:
        result = agent(
            request,
            context=AgentExecutionContext(
                run_id="run-integration",
                session_id="session-integration",
                dataset_profile=prepared.dataset_profile,
                duckdb_context=prepared.duckdb_context,
                output_dir=str(repo_tmp_path / "artifacts"),
            ),
        )
    finally:
        prepared.duckdb_context.close()

    assert result.narrative == "Narrativa integrada"
    assert result.artifact_manifest.run_id == "run-integration"
    assert result.artifact_manifest.table_paths == []
    assert result.artifact_manifest.chart_paths == []
    assert result.charts == []
    assert [table.name for table in result.tables] == ["preview", "numeric_summary"]
    assert result.tables[0].rows[0]["store"] == 1
    assert {row["column_name"] for row in result.tables[1].rows} == {"store", "weekly_sales", "temperature"}
    assert len(result.sql_trace) == 2
    assert all(entry.status.value == "ok" for entry in result.sql_trace)
    assert any("Dataset has 3 rows and 4 columns." == finding for finding in result.findings)
    assert llm.prompts and "Resume ventas y temperatura" in llm.prompts[0]
