"""Minimal agent registry for the MVP runtime."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from application.contracts import AgentExecutionContext, AgentResult, ErrorStage, RunError, RunRequest
from agents.data_analyst import (
    DATA_ANALYST_AGENT_CONFIG,
    DATA_ANALYST_AGENT_ID,
    build_default_data_analyst_executor,
)

AgentExecutor = Callable[[RunRequest, AgentExecutionContext], AgentResult]


def _require_non_empty_string(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty string")

    return normalized


@dataclass(slots=True)
class RegisteredAgent:
    """Static runtime registration for an available MVP agent."""

    agent_id: str
    executor: AgentExecutor
    config: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.agent_id = _require_non_empty_string(self.agent_id, "agent_id")
        if not callable(self.executor):
            raise TypeError("executor must be callable")
        self.config = dict(self.config)


class AgentRegistry:
    """Lightweight explicit registry for MVP agent resolution."""

    def __init__(self, agents: Mapping[str, RegisteredAgent]) -> None:
        self._agents = {str(agent_id): agent for agent_id, agent in agents.items()}

        if not self._agents:
            raise ValueError("agents must contain at least one registered agent")

        for agent_id, agent in self._agents.items():
            if agent_id != agent.agent_id:
                raise ValueError("registry keys must match RegisteredAgent.agent_id")

    @property
    def available_agent_ids(self) -> list[str]:
        return sorted(self._agents)

    def resolve(self, agent_id: str) -> RegisteredAgent:
        normalized_agent_id = _require_non_empty_string(agent_id, "agent_id")

        try:
            return self._agents[normalized_agent_id]
        except KeyError as exc:
            raise RunError(
                code="agent_not_found",
                message=f"Unknown agent_id: {normalized_agent_id}",
                stage=ErrorStage.AGENT_RESOLUTION,
                details={
                    "agent_id": normalized_agent_id,
                    "available_agent_ids": self.available_agent_ids,
                },
            ) from exc


def build_default_agent_registry() -> AgentRegistry:
    """Builds the static registry supported by the MVP."""

    return AgentRegistry(
        {
            DATA_ANALYST_AGENT_ID: RegisteredAgent(
                agent_id=DATA_ANALYST_AGENT_ID,
                executor=build_default_data_analyst_executor(),
                config=DATA_ANALYST_AGENT_CONFIG,
            )
        }
    )
