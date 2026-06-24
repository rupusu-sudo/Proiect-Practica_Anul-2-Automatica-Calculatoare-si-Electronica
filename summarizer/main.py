import time
import logging
from fastapi import FastAPI, status  # pyrefly: ignore [missing-import]
from shared.config import settings
from shared.utils import setup_logging, send_a2a_request
from shared.protocol import A2AMessage, A2AResponse
from shared.llm import get_llm_provider
from summarizer.processor import SummarizerProcessor

logger = setup_logging("summarizer")
llm_provider = get_llm_provider()
processor = SummarizerProcessor(llm=llm_provider)

app = FastAPI(
    title="A2A Summarizer Agent",
    description="Microserviciu de rezumare și extragere puncte cheie din text.",
    version="1.0.0",
)


@app.post("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "healthy", "agent": "summarizer", "llm_provider": settings.LLM_PROVIDER}


@app.get("/info", status_code=status.HTTP_200_OK)
async def get_info():
    return {
        "agent_name": "summarizer",
        "supported_tasks": ["summarize", "summarize_research"],
    }


@app.post("/task", response_model=A2AResponse, status_code=status.HTTP_200_OK)
async def handle_task(message: A2AMessage) -> A2AResponse:
    start_time = time.perf_counter()
    logger.info(f"Mesaj primit {message.message_id} de la {message.sender} solicitând '{message.task_type}'")

    if message.task_type not in ["summarize", "summarize_research"]:
        error_msg = f"Tipul de sarcină '{message.task_type}' nu este suportat. Suportat: ['summarize', 'summarize_research']"
        logger.error(error_msg)
        return A2AResponse(
            message_id=message.message_id, status="failed",
            processing_time=time.perf_counter() - start_time, error=error_msg,
        )

    try:
        # Faza 1: Rezumare/raportare
        summarizer_result = await processor.process_task(message.payload)
        
        # Dacă este vorba de cercetare, mergem în lanț A2A mai departe către ExportAgent
        if message.task_type == "summarize_research":
            export_msg = A2AMessage(
                sender="summarizer",
                receiver="exporter",
                task_type="export_document",
                priority=message.priority,
                payload={
                    "title": message.payload.get("title", "Cercetare"),
                    "report": summarizer_result.get("report", ""),
                    "summary": summarizer_result.get("summary", ""),
                    "key_points": summarizer_result.get("key_points", []),
                    "sources": message.payload.get("sources", []),
                    "verified_sources": message.payload.get("verified_sources", []),
                    "rejected_sources": message.payload.get("rejected_sources", []),
                    "trust_score": message.payload.get("trust_score", 70),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "workflow_metadata": {
                        "message_id": message.message_id,
                        "priority": message.priority
                    }
                }
            )
            
            logger.info(f"--> [Înlănțuire A2A] Trimitere date sintetizate către Exporter la {settings.export_url}")
            export_response = await send_a2a_request(
                target_url=settings.export_url,
                request_message=export_msg
            )
            
            processing_time = time.perf_counter() - start_time
            
            if export_response.status == "failed":
                logger.error(f"Faza de export documente a eșuat: {export_response.error}")
                return A2AResponse(
                    message_id=message.message_id,
                    status="failed",
                    processing_time=processing_time,
                    error=f"Eșec la export în lanț: {export_response.error}"
                )
                
            # Combinare rezultate
            final_result = {
                "title": message.payload.get("title", "Cercetare"),
                "summary": summarizer_result.get("summary", ""),
                "key_points": summarizer_result.get("key_points", []),
                "report": summarizer_result.get("report", ""),
                "trust_score": message.payload.get("trust_score", 70),
                "verified_sources": message.payload.get("verified_sources", []),
                "rejected_sources": message.payload.get("rejected_sources", []),
                "pdf_filename": export_response.result.get("pdf_filename"),
                "docx_filename": export_response.result.get("docx_filename"),
                "exporter_time": export_response.processing_time,
                "summarizer_time": processing_time - export_response.processing_time
            }
            
            logger.info(f"Lanțul complet A2A din Summarizer s-a finalizat în {processing_time:.4f}s")
            return A2AResponse(
                message_id=message.message_id,
                status="completed",
                processing_time=processing_time,
                result=final_result,
            )
            
        else:
            # Fluxul simplu de rezumare text
            processing_time = time.perf_counter() - start_time
            logger.info(f"Sarcina simplă {message.message_id} s-a finalizat în {processing_time:.4f}s")
            return A2AResponse(
                message_id=message.message_id, status="completed",
                processing_time=processing_time, result=summarizer_result,
            )
            
    except Exception as e:
        processing_time = time.perf_counter() - start_time
        error_msg = f"Eroare de procesare în Summarizer: {str(e)}"
        logger.exception(f"Sarcina {message.message_id} a eșuat: {error_msg}")
        return A2AResponse(
            message_id=message.message_id, status="failed",
            processing_time=processing_time, error=error_msg,
        )


if __name__ == "__main__":
    import uvicorn  # pyrefly: ignore [missing-import]
    uvicorn.run(app, host=settings.SUMMARIZER_HOST, port=settings.SUMMARIZER_PORT)
