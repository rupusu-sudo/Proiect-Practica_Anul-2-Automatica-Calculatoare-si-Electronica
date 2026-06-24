import time
import logging
from fastapi import FastAPI, status  # pyrefly: ignore [missing-import]
from shared.config import settings
from shared.utils import setup_logging
from shared.protocol import A2AMessage, A2AResponse
from shared.llm import get_llm_provider
from translator.processor import TranslatorProcessor

logger = setup_logging("translator")
llm_provider = get_llm_provider()
processor = TranslatorProcessor(llm=llm_provider)

app = FastAPI(
    title="A2A Translator Agent",
    description="Microservice for text translation across languages.",
    version="1.0.0",
)


@app.post("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "healthy", "agent": "translator", "llm_provider": settings.LLM_PROVIDER}


@app.get("/info", status_code=status.HTTP_200_OK)
async def get_info():
    return {
        "agent_name": "translator",
        "supported_tasks": ["translate"],
        "llm_provider": settings.LLM_PROVIDER,
        "model_name": settings.OPENAI_MODEL if settings.LLM_PROVIDER == "openai" else settings.OLLAMA_MODEL,
    }


@app.post("/task", response_model=A2AResponse, status_code=status.HTTP_200_OK)
async def handle_task(message: A2AMessage) -> A2AResponse:
    start_time = time.perf_counter()
    logger.info(f"Received message {message.message_id} from {message.sender} requesting '{message.task_type}'")

    if message.task_type != "translate":
        error_msg = f"Task type '{message.task_type}' not supported. Supported: ['translate']"
        logger.error(error_msg)
        return A2AResponse(
            message_id=message.message_id, status="failed",
            processing_time=time.perf_counter() - start_time, error=error_msg,
        )

    try:
        result = await processor.process_task(message.payload)
        processing_time = time.perf_counter() - start_time
        logger.info(f"Task {message.message_id} completed in {processing_time:.4f}s")
        return A2AResponse(
            message_id=message.message_id, status="completed",
            processing_time=processing_time, result=result,
        )
    except Exception as e:
        processing_time = time.perf_counter() - start_time
        error_msg = f"Translation error: {e}"
        logger.exception(f"Task {message.message_id} failed: {error_msg}")
        return A2AResponse(
            message_id=message.message_id, status="failed",
            processing_time=processing_time, error=error_msg,
        )


if __name__ == "__main__":
    import uvicorn  # pyrefly: ignore [missing-import]
    uvicorn.run(app, host=settings.TRANSLATOR_HOST, port=settings.TRANSLATOR_PORT)
