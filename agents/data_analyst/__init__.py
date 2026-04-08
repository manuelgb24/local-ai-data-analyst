"""Public exports for the real `data_analyst` MVP agent."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .agent import DataAnalystAgent

if TYPE_CHECKING:
    from adapters.ollama_adapter import OllamaLLMAdapter

DATA_ANALYST_AGENT_ID = "data_analyst"
DATA_ANALYST_AGENT_CONFIG = {"model": "deepseek-r1:8b"}


def build_data_analyst_llm_adapter(
    base_url: str | None = None,
    timeout_seconds: float | None = None,
) -> "OllamaLLMAdapter":
    """Build the fixed-model Ollama adapter reserved for the data_analyst agent."""

    from adapters.ollama_adapter import (
        DEFAULT_OLLAMA_BASE_URL,
        DEFAULT_OLLAMA_TIMEOUT_SECONDS,
        OllamaLLMAdapter,
    )

    return OllamaLLMAdapter(
        model=DATA_ANALYST_AGENT_CONFIG["model"],
        base_url=DEFAULT_OLLAMA_BASE_URL if base_url is None else base_url,
        timeout_seconds=DEFAULT_OLLAMA_TIMEOUT_SECONDS if timeout_seconds is None else timeout_seconds,
    )


def build_default_data_analyst_executor() -> DataAnalystAgent:
    """Build the real MVP `data_analyst` executor with the fixed LLM adapter."""

    return DataAnalystAgent(llm_adapter=build_data_analyst_llm_adapter())


__all__ = [
    "DataAnalystAgent",
    "DATA_ANALYST_AGENT_CONFIG",
    "DATA_ANALYST_AGENT_ID",
    "build_data_analyst_llm_adapter",
    "build_default_data_analyst_executor",
]
