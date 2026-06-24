import time
import logging
import asyncio
import httpx  # pyrefly: ignore [missing-import]
from shared.config import settings
from shared.protocol import A2AMessage, A2AResponse

logger = logging.getLogger("a2a")


def setup_logging(agent_name: str):
    """Configurează logarea structurată pentru un proces de tip agent."""
    agent_logger = logging.getLogger("a2a")
    agent_logger.setLevel(settings.LOG_LEVEL)

    if not agent_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt=f"[%(asctime)s] [%(levelname)s] [{agent_name.upper()}] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        agent_logger.addHandler(handler)
    return agent_logger


async def send_a2a_request(target_url: str, request_message: A2AMessage) -> A2AResponse:
    """Trimite un mesaj A2AMessage către agentul țintă cu logică de reîncercare (retry)."""
    url = f"{target_url.rstrip('/')}/task"
    payload = request_message.model_dump(mode="json")

    logger.info(
        f"--> TRIMITERE mesaj {request_message.message_id} | "
        f"Expeditor: {request_message.sender} | Destinatar: {request_message.receiver} | "
        f"Sarcină: {request_message.task_type} | Țintă: {url}"
    )

    start_time = time.perf_counter()

    async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
        for attempt in range(1, settings.MAX_RETRIES + 1):
            try:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    a2a_response = A2AResponse.model_validate(response.json())
                    duration = time.perf_counter() - start_time
                    logger.info(f"<-- RECEPȚIONAT Răspuns pentru {request_message.message_id} | Stare: {a2a_response.status} | Durată: {duration:.4f}s")
                    return a2a_response
                else:
                    logger.warning(f"HTTP {response.status_code} la încercarea {attempt} pentru {url}")
            except httpx.RequestError as exc:
                logger.error(f"Încercarea de conexiune {attempt}/{settings.MAX_RETRIES} a eșuat pentru {request_message.receiver} la {url}: {exc}")
            except Exception as exc:
                logger.error(f"Eroare neașteptată la încercarea {attempt}: {exc}")

            if attempt < settings.MAX_RETRIES:
                sleep_time = settings.BACKOFF_FACTOR ** attempt
                logger.info(f"Reîncercare în {sleep_time:.2f}s...")
                await asyncio.sleep(sleep_time)

    duration = time.perf_counter() - start_time
    error_msg = f"Eșec la comunicarea cu {request_message.receiver} după {settings.MAX_RETRIES} încercări la {url}."
    logger.error(error_msg)
    return A2AResponse(
        message_id=request_message.message_id,
        status="failed",
        processing_time=duration,
        error=error_msg,
    )
