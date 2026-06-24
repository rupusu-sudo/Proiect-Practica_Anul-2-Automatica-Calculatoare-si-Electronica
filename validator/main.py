import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, status  # pyrefly: ignore [missing-import]
from shared.config import settings
from shared.protocol import A2AMessage, A2AResponse
from shared.utils import setup_logging, send_a2a_request
from validator.processor import SourceValidatorProcessor

logger = setup_logging("validator")
processor = SourceValidatorProcessor()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=================================================================")
    logger.info(f"Agentul de Validare Surse pornește pe {settings.VALIDATOR_HOST}:{settings.VALIDATOR_PORT}")
    logger.info(f"Agent de Rezumare aval: {settings.summarizer_url}")
    logger.info("=================================================================")
    yield


app = FastAPI(
    title="A2A Source Validator Agent",
    description="Agent responsabil cu analiza credibilității surselor bibliografice.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "healthy", "agent": "validator"}


@app.get("/info", status_code=status.HTTP_200_OK)
async def get_info():
    return {
        "agent_name": "validator",
        "supported_tasks": ["validate_sources"],
    }


@app.post("/task", response_model=A2AResponse, status_code=status.HTTP_200_OK)
async def handle_task(message: A2AMessage) -> A2AResponse:
    start_time = time.perf_counter()
    logger.info(f"Mesaj primit {message.message_id} de la {message.sender} cu sarcina '{message.task_type}'")

    if message.task_type != "validate_sources":
        error_msg = f"Sarcina '{message.task_type}' nu este suportată de Agentul de Validare Surse."
        logger.error(error_msg)
        return A2AResponse(
            message_id=message.message_id,
            status="failed",
            processing_time=time.perf_counter() - start_time,
            error=error_msg,
        )

    try:
        # Faza 1: Validare surse
        validation_result = processor.process_task(message.payload)
        
        # Faza 2: Înlănțuire directă A2A către SummarizerAgent
        summarizer_msg = A2AMessage(
            sender="validator",
            receiver="summarizer",
            task_type="summarize_research",
            priority=message.priority,
            payload={
                "query": message.payload.get("query"),
                "result_type": message.payload.get("result_type", "Rezumat"),
                "title": message.payload.get("title"),
                "facts": message.payload.get("facts"),
                "sources": validation_result["verified_sources"],  # trimitem doar cele verificate pentru sinteză
                "verified_sources": validation_result["verified_sources"],
                "rejected_sources": validation_result["rejected_sources"],
                "trust_score": validation_result["trust_score"]
            }
        )
        
        logger.info(f"--> [Înlănțuire A2A] Trimitere date validate către Summarizer la {settings.summarizer_url}")
        summarizer_response = await send_a2a_request(
            target_url=settings.summarizer_url,
            request_message=summarizer_msg
        )
        
        processing_time = time.perf_counter() - start_time
        
        if summarizer_response.status == "failed":
            logger.error(f"Faza de rezumare în lanț a eșuat: {summarizer_response.error}")
            return A2AResponse(
                message_id=message.message_id,
                status="failed",
                processing_time=processing_time,
                error=f"Eșec la rezumare în lanț: {summarizer_response.error}"
            )
            
        # Adăugare date specifice de validare la răspunsul final
        final_result = summarizer_response.result
        final_result["validator_time"] = processing_time - summarizer_response.processing_time
        
        logger.info(f"Fluxul în lanț de validare s-a finalizat în {processing_time:.4f}s")
        return A2AResponse(
            message_id=message.message_id,
            status="completed",
            processing_time=processing_time,
            result=final_result,
        )

    except Exception as e:
        processing_time = time.perf_counter() - start_time
        error_msg = f"Eroare în lanțul de validare: {str(e)}"
        logger.exception(f"Sarcina {message.message_id} a eșuat: {error_msg}")
        return A2AResponse(
            message_id=message.message_id,
            status="failed",
            processing_time=processing_time,
            error=error_msg,
        )


if __name__ == "__main__":
    import uvicorn  # pyrefly: ignore [missing-import]
    uvicorn.run(app, host=settings.VALIDATOR_HOST, port=settings.VALIDATOR_PORT)
