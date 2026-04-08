import pytest

from agents.data_analyst import DataAnalystAgent
from application import AgentExecutionContext, AgentResult, ArtifactManifest, ErrorStage, RunError, RunRequest
from runtime import AgentRegistry, RegisteredAgent, build_default_agent_registry


def fake_agent_executor(request: RunRequest, context: AgentExecutionContext) -> AgentResult:
    return AgentResult(
        narrative="ok",
        findings=[],
        sql_trace=[],
        tables=[],
        charts=[],
        artifact_manifest=ArtifactManifest(run_id=context.run_id),
    )


def test_default_agent_registry_resolves_data_analyst() -> None:
    registry = build_default_agent_registry()

    registered_agent = registry.resolve("data_analyst")

    assert registered_agent.agent_id == "data_analyst"
    assert registered_agent.config == {"model": "deepseek-r1:8b"}
    assert isinstance(registered_agent.executor, DataAnalystAgent)


def test_agent_registry_rejects_unknown_agent_with_stable_error() -> None:
    registry = build_default_agent_registry()

    with pytest.raises(RunError) as exc_info:
        registry.resolve("unknown_agent")

    assert exc_info.value.code == "agent_not_found"
    assert exc_info.value.message == "Unknown agent_id: unknown_agent"
    assert exc_info.value.stage is ErrorStage.AGENT_RESOLUTION
    assert exc_info.value.details == {
        "agent_id": "unknown_agent",
        "available_agent_ids": ["data_analyst"],
    }


def test_agent_registry_exposes_only_registered_agent_ids() -> None:
    registry = AgentRegistry(
        {
            "data_analyst": RegisteredAgent(
                agent_id="data_analyst",
                executor=fake_agent_executor,
                config={"model": "deepseek-r1:8b"},
            )
        }
    )

    assert registry.available_agent_ids == ["data_analyst"]
