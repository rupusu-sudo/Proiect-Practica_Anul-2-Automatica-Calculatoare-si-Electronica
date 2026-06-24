import pytest  # pyrefly: ignore [missing-import]
import uuid
import os
from unittest.mock import AsyncMock, patch
from shared.protocol import A2AMessage, A2AResponse
from shared.database import init_db, save_research_history, save_validation_history, save_export_event, get_all_research_history, get_system_metrics, DB_PATH
from researcher.processor import ResearchProcessor
from validator.processor import SourceValidatorProcessor
from exporter.processor import ExportProcessor, EXPORT_DIR

@pytest.fixture(autouse=True)
def setup_test_db():
    # Ștergem baza de date de test anterioară dacă există
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except Exception:
            pass
    init_db()
    yield
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except Exception:
            pass


def test_sqlite_database_persistence():
    """Verifică salvarea și regăsirea datelor din SQLite."""
    research_id = save_research_history(
        query="Test Query",
        summary="Test Summary Content",
        sources_count=3
    )
    assert research_id is not None
    
    save_validation_history(
        research_id=research_id,
        trust_score=91,
        validated_sources=["https://wikipedia.org/wiki/Turing"]
    )
    
    save_export_event("pdf")
    
    history = get_all_research_history()
    assert len(history) == 1
    assert history[0]["query"] == "Test Query"
    
    metrics = get_system_metrics()
    assert metrics["avg_trust_score"] == 91
    assert metrics["generated_documents"] == 1
    assert metrics["validated_sources"] == 1


@pytest.mark.asyncio
async def test_research_processor_fallback():
    """Verifică dacă procesorul de cercetare aplică fallback-ul corect pentru subiecte predefinite."""
    mock_llm = AsyncMock()
    mock_llm.generate.side_effect = Exception("Connection error")
    
    processor = ResearchProcessor(llm=mock_llm)
    result = await processor.process_task({"query": "Alan Turing"})
    
    assert result["title"] == "Alan Turing"
    assert len(result["facts"]) == 5
    assert len(result["sources"]) == 3


def test_source_validator_scoring():
    """Verifică calcularea corectă a trust score-ului de către SourceValidatorProcessor."""
    processor = SourceValidatorProcessor()
    
    # Test 1: Doar surse academice și de încredere mare
    payload = {
        "sources": [
            "https://en.wikipedia.org/wiki/Turing",
            "https://nature.com/articles/123",
            "https://mit.edu/research"
        ]
    }
    result = processor.process_task(payload)
    assert result["trust_score"] == 95
    assert len(result["verified_sources"]) == 3
    assert len(result["rejected_sources"]) == 0
    
    # Test 2: Surse mixte (academice + bloguri)
    payload_mixed = {
        "sources": [
            "https://mit.edu/research",
            "https://myblog.wordpress.com/post1",
            "https://reddit.com/r/science"
        ]
    }
    result_mixed = processor.process_task(payload_mixed)
    assert result_mixed["trust_score"] < 70
    assert len(result_mixed["verified_sources"]) == 1
    assert len(result_mixed["rejected_sources"]) == 2


def test_export_processor_generation():
    """Verifică generarea fizică a fișierelor PDF și DOCX de către ExportProcessor."""
    processor = ExportProcessor()
    payload = {
        "title": "Calcul Cuantic",
        "summary": "Rezumat test",
        "key_points": ["Punctul 1", "Punctul 2"],
        "report": "Eseu academic despre calculul cuantic...",
        "sources": ["https://nature.com"],
        "trust_score": 95,
        "timestamp": "2026-06-24",
        "workflow_metadata": {"id": "123"}
    }
    
    result = processor.process_task(payload)
    
    assert os.path.exists(result["pdf_filepath"])
    assert os.path.exists(result["docx_filepath"])
    
    # Curățăm fișierele create după test
    try:
        os.remove(result["pdf_filepath"])
        os.remove(result["docx_filepath"])
    except Exception:
        pass
