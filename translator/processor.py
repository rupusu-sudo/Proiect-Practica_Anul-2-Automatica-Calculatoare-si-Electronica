import logging
from typing import Dict, Any
from shared.llm import BaseLLM, strip_markdown_fences

logger = logging.getLogger("a2a.translator")


class TranslatorProcessor:
    """Procesează traducerea unui text într-o limbă țintă prin LLM."""

    def __init__(self, llm: BaseLLM):
        self.llm = llm

    async def process_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        text = payload.get("text")
        target_language = payload.get("target_language")

        if not text:
            raise ValueError("Lipsește câmpul 'text' din payload-ul de traducere.")
        if not target_language:
            raise ValueError("Lipsește câmpul 'target_language' din payload-ul de traducere.")

        system_prompt = (
            f"You are an expert translation agent. Your task is to translate the user text into {target_language}. "
            "Provide only the translation itself. Maintain the professional tone of the input. "
            "Do not include any introductory remarks, conversation context, explanations, or markdown code block wrapper formatting."
        )
        user_prompt = f"Translate the following text:\n\n{text}"

        logger.info(f"Trimitere cerere de traducere către LLM. Limba țintă: {target_language}")
        translated_text = await self.llm.generate(prompt=user_prompt, system_prompt=system_prompt)

        return {
            "translated_text": strip_markdown_fences(translated_text),
            "target_language": target_language,
        }
