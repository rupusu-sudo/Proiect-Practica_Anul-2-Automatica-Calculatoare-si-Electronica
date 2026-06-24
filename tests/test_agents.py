import pytest  # pyrefly: ignore [missing-import]
from typing import Optional
from shared.llm import BaseLLM
from summarizer.processor import SummarizerProcessor
from translator.processor import TranslatorProcessor

class MockLLM(BaseLLM):
    """
    Mock LLM provider that returns predetermined responses based on configured outputs.
    """
    def __init__(self, response_text: str):
        self.response_text = response_text
        self.last_prompt: Optional[str] = None
        self.last_system_prompt: Optional[str] = None

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        self.last_prompt = prompt
        self.last_system_prompt = system_prompt
        return self.response_text


@pytest.mark.asyncio
async def test_summarizer_processor_success():
    """Tests SummarizerProcessor with structured JSON LLM output."""
    mock_json_output = '{"summary": "This is a summary.", "key_points": ["Point 1", "Point 2"]}'
    mock_llm = MockLLM(mock_json_output)
    processor = SummarizerProcessor(llm=mock_llm)

    payload = {"text": "A long text that needs summarization."}
    result = await processor.process_task(payload)

    assert result["summary"] == "This is a summary."
    assert result["key_points"] == ["Point 1", "Point 2"]
    assert mock_llm.last_system_prompt is not None
    assert "You are an expert text summarization agent" in mock_llm.last_system_prompt


@pytest.mark.asyncio
async def test_summarizer_processor_fallback():
    """Tests SummarizerProcessor fallback logic when LLM output is not valid JSON."""
    mock_raw_text = "This is a fallback summary.\n- Key Point A\n- Key Point B"
    mock_llm = MockLLM(mock_raw_text)
    processor = SummarizerProcessor(llm=mock_llm)

    payload = {"text": "A long text that needs summarization."}
    result = await processor.process_task(payload)

    assert result["summary"] == "This is a fallback summary."
    assert "Key Point A" in result["key_points"]
    assert "Key Point B" in result["key_points"]


@pytest.mark.asyncio
async def test_translator_processor_success():
    """Tests TranslatorProcessor translates text correctly."""
    mock_translation = "Hola Mundo"
    mock_llm = MockLLM(mock_translation)
    processor = TranslatorProcessor(llm=mock_llm)

    payload = {"text": "Hello World", "target_language": "Spanish"}
    result = await processor.process_task(payload)

    assert result["translated_text"] == "Hola Mundo"
    assert result["target_language"] == "Spanish"
    assert mock_llm.last_system_prompt is not None
    assert "translate the user text into Spanish" in mock_llm.last_system_prompt
    assert mock_llm.last_prompt == "Translate the following text:\n\nHello World"
