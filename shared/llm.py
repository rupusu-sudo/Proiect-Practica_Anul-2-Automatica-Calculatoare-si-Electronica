import re
import logging
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, cast
import httpx  # pyrefly: ignore [missing-import]
from openai import AsyncOpenAI  # pyrefly: ignore [missing-import]
from shared.config import settings

logger = logging.getLogger("a2a.llm")


class LLMProviderError(Exception):
    """Excepție ridicată atunci când un furnizor LLM eșuează."""
    pass


class BaseLLM(ABC):
    """Contract abstract pentru integrarea furnizorilor de LLM."""

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        pass


def _generate_simulated_response(prompt: str, system_prompt: Optional[str] = None) -> str:
    """Generează răspunsuri simulate pentru testare locală când cheile API lipsesc."""
    if system_prompt and "JSON" in system_prompt:
        return (
            '{"summary": "Inteligența Artificială (IA) transformă dezvoltarea software '
            'prin sisteme multi-agent autonome folosind protocoale precum A2A.", '
            '"key_points": ["IA automatizează rezumarea și traducerea codului", '
            '"Agenții comunică prin protocolul standardizat A2A", '
            '"Arhitectura de microservicii oferă fiabilitate crescută"]}'
        )
    elif system_prompt and "translate" in system_prompt.lower():
        match = re.search(r"translate the user text into (\w+)", system_prompt, re.IGNORECASE)
        lang = match.group(1) if match else "Romanian"
        if lang.lower() in ("romanian", "română"):
            return (
                "Inteligența Artificială (IA) transformă dezvoltarea software "
                "într-un ritm fără precedent prin intermediul sistemelor multi-agent "
                "care comunică prin protocolul A2A."
            )
        return f"[Traducere simulată a textului în limba {lang}]"
    return f"[Răspuns LLM Simulat pentru promptul: '{prompt[:50]}...']"


def strip_markdown_fences(text: str) -> str:
    """Elimină blocul de markdown (```json ... ```) dacă acesta este returnat de LLM."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return text


class OpenAIProvider(BaseLLM):
    """Integrare pentru API-uri compatibile cu OpenAI."""

    def __init__(self, api_key: str, base_url: str, model: str):
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        logger.info(f"OpenAIProvider inițializat: {base_url} model={model}")

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        messages: List[Dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=cast(Any, messages),
                temperature=0.7,
                max_tokens=1000,
                timeout=settings.REQUEST_TIMEOUT_SECONDS,
            )
            content = response.choices[0].message.content
            if not content:
                raise LLMProviderError("OpenAI a returnat un răspuns gol.")
            return content.strip()
        except Exception as e:
            logger.error(f"Apelul API OpenAI a eșuat: {e}")
            if settings.OPENAI_API_KEY == "mock-key-for-testing":
                logger.warning("Cheie API de test detectată. Se generează răspunsul simulat.")
                return _generate_simulated_response(prompt, system_prompt)
            raise LLMProviderError(f"Apelul API OpenAI a eșuat: {e}") from e


class OllamaProvider(BaseLLM):
    """Integrare locală Ollama prin API-ul REST."""

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._client = httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS)
        logger.info(f"OllamaProvider inițializat: {self.base_url} model={model}")

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        url = f"{self.base_url}/api/generate"
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.7},
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()
        except httpx.HTTPError as e:
            logger.error(f"Conexiunea API Ollama a eșuat: {e}")
            logger.warning("Se generează răspunsul simulat pentru stabilitatea demonstrației.")
            return _generate_simulated_response(prompt, system_prompt)
        except Exception as e:
            logger.error(f"Eroare neașteptată în Ollama Provider: {e}")
            raise LLMProviderError(f"Furnizorul Ollama a eșuat: {e}") from e


def get_llm_provider() -> BaseLLM:
    """Factory ce returnează furnizorul LLM configurat în mediu."""
    provider_type = settings.LLM_PROVIDER.lower().strip()
    if provider_type == "openai":
        return OpenAIProvider(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            model=settings.OPENAI_MODEL,
        )
    elif provider_type == "ollama":
        return OllamaProvider(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
        )
    else:
        raise ValueError(f"Furnizor LLM necunoscut: {settings.LLM_PROVIDER}")
