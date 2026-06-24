import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI  # pyrefly: ignore [missing-import]
from shared.config import settings
from shared.utils import setup_logging
from coordinator.router import router as coordinator_router

logger = setup_logging("coordinator")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=================================================================")
    logger.info(f"Agentul Coordonator pornește pe {settings.COORDINATOR_HOST}:{settings.COORDINATOR_PORT}")
    logger.info(f"Furnizor LLM configurat: {settings.LLM_PROVIDER.upper()}")
    logger.info(f"Agent Rezumare aval: {settings.summarizer_url}")
    logger.info(f"Agent Traducere aval: {settings.translator_url}")
    logger.info(f"Agent Cercetare aval: {settings.researcher_url}")
    logger.info("=================================================================")
    yield


app = FastAPI(
    title="A2A Coordinator Agent",
    description="Agent orchestrator pentru fluxuri de execuție multi-agent.",
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(coordinator_router)

if __name__ == "__main__":
    import uvicorn  # pyrefly: ignore [missing-import]
    uvicorn.run(app, host=settings.COORDINATOR_HOST, port=settings.COORDINATOR_PORT)
