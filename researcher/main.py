import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, status  # pyrefly: ignore [missing-import]
from shared.config import settings
from shared.protocol import A2AMessage, A2AResponse
from shared.utils import setup_logging, send_a2a_request
from shared.llm import get_llm_provider
from researcher.processor import ResearchProcessor

logger = setup_logging("researcher")
llm = get_llm_provider()
processor = ResearchProcessor(llm=llm)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=================================================================")
    logger.info(f"Agentul de Cercetare pornește pe {settings.RESEARCHER_HOST}:{settings.RESEARCHER_PORT}")
    logger.info(f"Furnizor LLM configurat: {settings.LLM_PROVIDER.upper()}")
    logger.info(f"Agent de Validare aval: {settings.validator_url}")
    logger.info("=================================================================")
    yield


app = FastAPI(
    title="A2A Research Agent",
    description="Agent responsabil cu colectarea de fapte și surse web despre un subiect.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "healthy", "agent": "researcher"}


@app.get("/info", status_code=status.HTTP_200_OK)
async def get_info():
    return {
        "agent_name": "researcher",
        "supported_tasks": ["research"],
    }


@app.post("/task", response_model=A2AResponse, status_code=status.HTTP_200_OK)
async def handle_task(message: A2AMessage) -> A2AResponse:
    start_time = time.perf_counter()
    logger.info(f"Mesaj primit {message.message_id} de la {message.sender} cu sarcina '{message.task_type}'")

    if message.task_type != "research":
        error_msg = f"Sarcina '{message.task_type}' nu este suportată de Agentul de Cercetare."
        logger.error(error_msg)
        return A2AResponse(
            message_id=message.message_id,
            status="failed",
            processing_time=time.perf_counter() - start_time,
            error=error_msg,
        )

    try:
        # Faza 1: Cercetare fapte + surse
        research_result = await processor.process_task(message.payload)
        
        # Faza 2: Înlănțuire directă A2A către SourceValidatorAgent
        validator_msg = A2AMessage(
            sender="researcher",
            receiver="validator",
            task_type="validate_sources",
            priority=message.priority,
            payload={
                "query": message.payload.get("query"),
                "result_type": message.payload.get("result_type", "Rezumat"),
                "title": research_result["title"],
                "facts": research_result["facts"],
                "sources": research_result["sources"]
            }
        )
        
        logger.info(f"--> [Înlănțuire A2A] Trimitere surse către Validator la {settings.validator_url}")
        validator_response = await send_a2a_request(
            target_url=settings.validator_url,
            request_message=validator_msg
        )
        
        processing_time = time.perf_counter() - start_time
        
        if validator_response.status == "failed":
            logger.error(f"Faza de validare surse în lanț a eșuat: {validator_response.error}")
            return A2AResponse(
                message_id=message.message_id,
                status="failed",
                processing_time=processing_time,
                error=f"Eșec la validare în lanț: {validator_response.error}"
            )
            
        logger.info(f"Fluxul în lanț de cercetare s-a întors prin Researcher în {processing_time:.4f}s")
        return A2AResponse(
            message_id=message.message_id,
            status="completed",
            processing_time=processing_time,
            result=validator_response.result,
        )

    except Exception as e:
        processing_time = time.perf_counter() - start_time
        error_msg = f"Eroare în lanțul de cercetare: {str(e)}"
        logger.exception(f"Sarcina {message.message_id} a eșuat: {error_msg}")
        return A2AResponse(
            message_id=message.message_id,
            status="failed",
            processing_time=processing_time,
            error=error_msg,
        )


if __name__ == "__main__":
    import uvicorn  # pyrefly: ignore [missing-import]
    uvicorn.run(app, host=settings.RESEARCHER_HOST, port=settings.RESEARCHER_PORT)
