import pytest  # pyrefly: ignore [missing-import]
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient  # pyrefly: ignore [missing-import]
from shared.protocol import A2AResponse
from coordinator.main import app as coordinator_app
from coordinator.orchestrator import CoordinatorOrchestrator

client = TestClient(coordinator_app)


@pytest.mark.asyncio
async def test_coordinator_orchestrator_success():
    """Verifies that orchestrator aggregates summarizer + translator responses correctly."""
    orchestrator = CoordinatorOrchestrator()

    mock_summarizer_response = A2AResponse(
        message_id="a8b8c8d8-e8f8-48a8-b8c8-d8e8f8a8b8c8",
        status="completed",
        processing_time=0.45,
        result={"summary": "Artificial intelligence is expanding.", "key_points": ["AI growth", "Tech impact"]},
    )
    mock_translator_response = A2AResponse(
        message_id="f8e8d8c8-b8a8-48f8-e8d8-c8b8a8f8e8d8",
        status="completed",
        processing_time=0.32,
        result={"translated_text": "La inteligencia artificial se está expandiendo.", "target_language": "Spanish"},
    )

    # Patch where the names are looked up (orchestrator module), not where they're defined (services module)
    with patch("coordinator.orchestrator.call_summarizer", new_callable=AsyncMock) as mock_sum, \
         patch("coordinator.orchestrator.call_translator", new_callable=AsyncMock) as mock_trans:

        mock_sum.return_value = mock_summarizer_response
        mock_trans.return_value = mock_translator_response

        payload = {
            "text": "Artificial intelligence is expanding rapidly in modern software engineering.",
            "target_language": "Spanish",
        }
        result = await orchestrator.execute_workflow(payload, priority=3)

        assert result["original_character_count"] == 76
        assert result["original_summary"] == "Artificial intelligence is expanding."
        assert result["key_points"] == ["AI growth", "Tech impact"]
        assert result["translated_text"] == "La inteligencia artificial se está expandiendo."
        assert result["target_language"] == "Spanish"
        assert result["summarizer_time"] == 0.45
        assert result["translator_time"] == 0.32
        assert "total_processing_time" in result

        mock_sum.assert_called_once()
        mock_trans.assert_called_once()


@pytest.mark.asyncio
async def test_coordinator_orchestrator_agent_failure():
    """Verifies orchestrator raises RuntimeError when summarizer reports failure."""
    orchestrator = CoordinatorOrchestrator()

    mock_summarizer_failure = A2AResponse(
        message_id="a8b8c8d8-e8f8-48a8-b8c8-d8e8f8a8b8c8",
        status="failed",
        processing_time=0.1,
        error="LLM Connection Timeout",
    )

    with patch("coordinator.orchestrator.call_summarizer", new_callable=AsyncMock) as mock_sum:
        mock_sum.return_value = mock_summarizer_failure

        payload = {"text": "Failed text document", "target_language": "French"}

        with pytest.raises(RuntimeError) as excinfo:
            await orchestrator.execute_workflow(payload)
        assert "Agentul de Rezumare a eșuat: LLM Connection Timeout" in str(excinfo.value)


def test_coordinator_health_endpoint():
    response = client.post("/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "healthy"
    assert json_data["agent"] == "coordinator"


def test_coordinator_info_endpoint():
    response = client.get("/info")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["agent_name"] == "coordinator"
    assert "orchestrate" in json_data["supported_tasks"]


def test_coordinator_ui_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Platformă de Cercetare & Monitorizare Multi-Agent A2A" in response.text
