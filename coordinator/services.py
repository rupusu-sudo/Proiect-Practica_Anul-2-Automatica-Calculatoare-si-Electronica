import logging
from shared.config import settings
from shared.protocol import A2AMessage, A2AResponse
from shared.utils import send_a2a_request

logger = logging.getLogger("a2a.coordinator.services")


async def call_summarizer(text: str, priority: int = 3) -> A2AResponse:
    """Trimite cererea de rezumare către Agentul de Rezumare."""
    request_msg = A2AMessage(
        sender="coordinator",
        receiver="summarizer",
        task_type="summarize",
        priority=priority,
        payload={"text": text},
    )
    logger.info(f"Rutare sarcină 'summarize' către Agentul de Rezumare la {settings.summarizer_url}")
    return await send_a2a_request(target_url=settings.summarizer_url, request_message=request_msg)


async def call_translator(text: str, target_language: str, priority: int = 3) -> A2AResponse:
    """Trimite cererea de traducere către Agentul de Traducere."""
    request_msg = A2AMessage(
        sender="coordinator",
        receiver="translator",
        task_type="translate",
        priority=priority,
        payload={"text": text, "target_language": target_language},
    )
    logger.info(f"Rutare sarcină 'translate' ({target_language}) către Agentul de Traducere la {settings.translator_url}")
    return await send_a2a_request(target_url=settings.translator_url, request_message=request_msg)


async def call_researcher(query: str, result_type: str, priority: int = 3) -> A2AResponse:
    """Trimite cererea de cercetare către Agentul de Cercetare (care va apela apoi în lanț Agentul de Validare Surse)."""
    request_msg = A2AMessage(
        sender="coordinator",
        receiver="researcher",
        task_type="research",
        priority=priority,
        payload={"query": query, "result_type": result_type},
    )
    logger.info(f"Rutare sarcină 'research' ({query}) către Agentul de Cercetare la {settings.researcher_url}")
    return await send_a2a_request(target_url=settings.researcher_url, request_message=request_msg)


async def call_validator(sources: list, priority: int = 3) -> A2AResponse:
    """Trimite cererea de validare a surselor către Agentul de Validare."""
    request_msg = A2AMessage(
        sender="coordinator",
        receiver="validator",
        task_type="validate_sources",
        priority=priority,
        payload={"sources": sources},
    )
    logger.info(f"Rutare sarcină 'validate_sources' către Agentul de Validare la {settings.validator_url}")
    return await send_a2a_request(target_url=settings.validator_url, request_message=request_msg)


async def call_exporter(payload: dict, priority: int = 3) -> A2AResponse:
    """Trimite cererea de export document către Agentul de Export."""
    request_msg = A2AMessage(
        sender="coordinator",
        receiver="exporter",
        task_type="export_document",
        priority=priority,
        payload=payload,
    )
    logger.info(f"Rutare sarcină 'export_document' ({payload.get('format')}) către Agentul de Export la {settings.export_url}")
    return await send_a2a_request(target_url=settings.export_url, request_message=request_msg)
