import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, status  # pyrefly: ignore [missing-import]
from shared.config import settings
from shared.protocol import A2AMessage, A2AResponse
from shared.utils import setup_logging
from exporter.processor import ExportProcessor

logger = setup_logging("exporter")
processor = ExportProcessor()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=================================================================")
    logger.info(f"Agentul de Export Documente pornește pe {settings.EXPORT_HOST}:{settings.EXPORT_PORT}")
    logger.info("=================================================================")
    yield


app = FastAPI(
    title="A2A Export Agent",
    description="Agent responsabil cu generarea fișierelor academice PDF și DOCX.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "healthy", "agent": "exporter"}


@app.get("/info", status_code=status.HTTP_200_OK)
async def get_info():
    return {
        "agent_name": "exporter",
        "supported_tasks": ["export_document"],
    }


@app.post("/task", response_model=A2AResponse, status_code=status.HTTP_200_OK)
async def handle_task(message: A2AMessage) -> A2AResponse:
    start_time = time.perf_counter()
    logger.info(f"Mesaj primit {message.message_id} de la {message.sender} cu sarcina '{message.task_type}'")

    if message.task_type != "export_document":
        error_msg = f"Sarcina '{message.task_type}' nu este suportată de Agentul de Export."
        logger.error(error_msg)
        return A2AResponse(
            message_id=message.message_id,
            status="failed",
            processing_time=time.perf_counter() - start_time,
            error=error_msg,
        )

    try:
        result = processor.process_task(message.payload)
        processing_time = time.perf_counter() - start_time
        logger.info(f"Sarcina de export {message.message_id} s-a finalizat în {processing_time:.4f}s")
        return A2AResponse(
            message_id=message.message_id,
            status="completed",
            processing_time=processing_time,
            result=result,
        )
    except Exception as e:
        processing_time = time.perf_counter() - start_time
        error_msg = f"Eroare procesare export: {str(e)}"
        logger.exception(f"Sarcina {message.message_id} a eșuat: {error_msg}")
        return A2AResponse(
            message_id=message.message_id,
            status="failed",
            processing_time=processing_time,
            error=error_msg,
        )


if __name__ == "__main__":
    import uvicorn  # pyrefly: ignore [missing-import]
    uvicorn.run(app, host=settings.EXPORT_HOST, port=settings.EXPORT_PORT)
