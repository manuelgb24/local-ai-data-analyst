import pytest

from agents.data_analyst import DATA_ANALYST_AGENT_CONFIG, build_data_analyst_llm_adapter
from application import RunError
from tests.smoke._ollama_ready import require_installed_model, require_ready_ollama


SMOKE_GENERATION_TIMEOUT_SECONDS = 120.0


@pytest.mark.smoke
def test_ollama_adapter_roundtrip_with_real_local_service() -> None:
    require_ready_ollama()
    require_installed_model()

    adapter = build_data_analyst_llm_adapter(
        timeout_seconds=SMOKE_GENERATION_TIMEOUT_SECONDS,
    )

    try:
        response = adapter.generate("Responde solo con OK.")
    except RunError as error:
        if error.code == "llm_provider_unavailable":
            pytest.skip(
                "Ollama dejó de estar disponible durante el smoke del adapter aun estando listo al inicio. "
                f"Detalle: {error.details}"
            )
        if error.code == "llm_generation_failed":
            pytest.fail(
                "Ollama estaba listo al inicio pero no pudo generar con el modelo fijo del MVP "
                f"({DATA_ANALYST_AGENT_CONFIG['model']}). Detalle: {error.details}"
            )
        raise

    assert response.strip()
