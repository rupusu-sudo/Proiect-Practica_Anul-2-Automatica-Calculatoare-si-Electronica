import os
import time
import logging
from fastapi import APIRouter, status, HTTPException  # pyrefly: ignore [missing-import]
from fastapi.responses import HTMLResponse, FileResponse  # pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field  # pyrefly: ignore [missing-import]
from shared.config import settings
from shared.protocol import A2AMessage, A2AResponse
from shared.database import get_all_research_history, get_system_metrics, save_export_event
from coordinator.orchestrator import CoordinatorOrchestrator

logger = logging.getLogger("a2a.coordinator.router")
router = APIRouter()
orchestrator = CoordinatorOrchestrator()

# Cale directă către directorul de export din rădăcina proiectului
EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "exports")
# Dacă EXPORT_DIR nu are calea corectă din cauza mutării în subdirectoare, o recalculăm:
EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports")
if not os.path.exists(EXPORT_DIR):
    # try project root
    EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "exports")

# Încărcare în cache a fișierului HTML pentru eficiență sporită
_HTML_PATH = os.path.join(os.path.dirname(__file__), "index.html")
with open(_HTML_PATH, "r", encoding="utf-8") as _f:
    _DASHBOARD_HTML = _f.read()


class SimpleOrchestrationRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50_000)
    target_language: str = Field(..., min_length=1, max_length=50)
    priority: int = Field(default=3, ge=1, le=5)


class SimpleResearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=100)
    result_type: str = Field(default="Rezumat", min_length=1, max_length=20)
    priority: int = Field(default=3, ge=1, le=5)


@router.post("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {
        "status": "healthy",
        "agent": "coordinator",
        "summarizer_endpoint": settings.summarizer_url,
        "translator_endpoint": settings.translator_url,
        "researcher_endpoint": settings.researcher_url,
        "validator_endpoint": settings.validator_url,
        "export_endpoint": settings.export_url,
    }


@router.get("/info", status_code=status.HTTP_200_OK)
async def get_info():
    return {
        "agent_name": "coordinator",
        "supported_tasks": ["orchestrate", "research"],
        "downstream_agents": ["summarizer", "translator", "researcher", "validator", "exporter"],
        "llm_provider": settings.LLM_PROVIDER,
    }


@router.post("/task", response_model=A2AResponse, status_code=status.HTTP_200_OK)
async def handle_task(message: A2AMessage) -> A2AResponse:
    start_time = time.perf_counter()
    logger.info(f"Mesaj recepționat {message.message_id} de la {message.sender} cu tipul de sarcină '{message.task_type}'")

    if message.task_type not in ["orchestrate", "research"]:
        error_msg = f"Tipul de sarcină '{message.task_type}' nu este suportat de Coordonator."
        logger.error(error_msg)
        return A2AResponse(
            message_id=message.message_id,
            status="failed",
            processing_time=time.perf_counter() - start_time,
            error=error_msg,
        )

    try:
        if message.task_type == "orchestrate":
            result = await orchestrator.execute_workflow(
                payload=message.payload, priority=message.priority
            )
        else:  # research
            result = await orchestrator.execute_research_workflow(
                payload=message.payload, priority=message.priority
            )
            
        processing_time = time.perf_counter() - start_time
        logger.info(f"Sarcina {message.message_id} s-a finalizat în {processing_time:.4f}s")
        return A2AResponse(
            message_id=message.message_id,
            status="completed",
            processing_time=processing_time,
            result=result,
        )
    except Exception as e:
        processing_time = time.perf_counter() - start_time
        error_msg = f"Eroare execuție task: {str(e)}"
        logger.exception(f"Sarcina {message.message_id} a eșuat: {error_msg}")
        return A2AResponse(
            message_id=message.message_id,
            status="failed",
            processing_time=processing_time,
            error=error_msg,
        )


@router.post("/orchestrate", response_model=A2AResponse, status_code=status.HTTP_200_OK)
async def simple_orchestrate(request: SimpleOrchestrationRequest) -> A2AResponse:
    start_time = time.perf_counter()

    internal_message = A2AMessage(
        sender="user",
        receiver="coordinator",
        task_type="orchestrate",
        priority=request.priority,
        payload={"text": request.text, "target_language": request.target_language},
    )
    logger.info(f"Solicitare orchestrare. ID mesaj intern: {internal_message.message_id}")

    try:
        result = await orchestrator.execute_workflow(
            payload=internal_message.payload, priority=internal_message.priority
        )
        processing_time = time.perf_counter() - start_time
        return A2AResponse(
            message_id=internal_message.message_id,
            status="completed",
            processing_time=processing_time,
            result=result,
        )
    except Exception as e:
        processing_time = time.perf_counter() - start_time
        return A2AResponse(
            message_id=internal_message.message_id,
            status="failed",
            processing_time=processing_time,
            error=f"Eroare orchestrare: {str(e)}",
        )


@router.post("/research", response_model=A2AResponse, status_code=status.HTTP_200_OK)
async def simple_research(request: SimpleResearchRequest) -> A2AResponse:
    start_time = time.perf_counter()

    internal_message = A2AMessage(
        sender="user",
        receiver="coordinator",
        task_type="research",
        priority=request.priority,
        payload={"query": request.query, "result_type": request.result_type},
    )
    logger.info(f"Solicitare cercetare pentru '{request.query}'. ID mesaj intern: {internal_message.message_id}")

    try:
        result = await orchestrator.execute_research_workflow(
            payload=internal_message.payload, priority=internal_message.priority
        )
        processing_time = time.perf_counter() - start_time
        return A2AResponse(
            message_id=internal_message.message_id,
            status="completed",
            processing_time=processing_time,
            result=result,
        )
    except Exception as e:
        processing_time = time.perf_counter() - start_time
        return A2AResponse(
            message_id=internal_message.message_id,
            status="failed",
            processing_time=processing_time,
            error=f"Eroare cercetare: {str(e)}",
        )


@router.get("/research/history", status_code=status.HTTP_200_OK)
async def get_research_history():
    try:
        history = get_all_research_history()
        return {"status": "success", "history": history}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/system/metrics", status_code=status.HTTP_200_OK)
async def get_metrics():
    """Returnează metricile avansate de sistem din baza de date SQLite."""
    try:
        metrics = get_system_metrics()
        return {"status": "success", "metrics": metrics}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/download/{filename}", status_code=status.HTTP_200_OK)
async def download_file(filename: str):
    """Servește descărcarea fișierelor academice pre-generate și contorizează exportul."""
    # Determinare cale fișier în directorul 'exports'
    # Folosim direct folderul de export determinat la pornirea modulului
    filepath = os.path.join(EXPORT_DIR, filename)
    
    if not os.path.exists(filepath):
        # încercare fallback în directoriu din rădăcină
        fallback_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "exports")
        filepath = os.path.join(fallback_dir, filename)

    if not os.path.exists(filepath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fișierul solicitat nu a fost găsit pe disc."
        )

    # Identificare format și înregistrare export în DB
    file_format = filename.split(".")[-1]
    save_export_event(file_format)
    logger.info(f"Descărcare fișier realizată cu succes: {filename}. Înregistrat eveniment în DB.")

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/octet-stream"
    )


@router.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    try:
        with open(_HTML_PATH, "r", encoding="utf-8") as _f:
            return HTMLResponse(content=_f.read())
    except Exception:
        return HTMLResponse(content=_DASHBOARD_HTML)
