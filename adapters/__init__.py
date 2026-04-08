"""Adapters layer public exports for the MVP."""

from .duckdb_adapter import DuckDBContext, create_duckdb_context
from .ollama_adapter import (
    DEFAULT_OLLAMA_COMMAND_TIMEOUT_SECONDS,
    DEFAULT_OLLAMA_BASE_URL,
    DEFAULT_OLLAMA_TIMEOUT_SECONDS,
    OllamaBinaryProbeResult,
    OllamaEndpointProbeResult,
    OllamaLLMAdapter,
    OllamaModelProbeResult,
    probe_ollama_binary,
    probe_ollama_endpoint,
    probe_ollama_model,
)

__all__ = [
    "DEFAULT_OLLAMA_COMMAND_TIMEOUT_SECONDS",
    "DEFAULT_OLLAMA_BASE_URL",
    "DEFAULT_OLLAMA_TIMEOUT_SECONDS",
    "DuckDBContext",
    "OllamaBinaryProbeResult",
    "OllamaEndpointProbeResult",
    "OllamaLLMAdapter",
    "OllamaModelProbeResult",
    "create_duckdb_context",
    "probe_ollama_binary",
    "probe_ollama_endpoint",
    "probe_ollama_model",
]
