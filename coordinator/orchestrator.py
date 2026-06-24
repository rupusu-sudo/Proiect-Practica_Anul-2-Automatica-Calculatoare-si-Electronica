import logging
import time
from typing import Dict, Any
from coordinator.services import call_summarizer, call_translator, call_researcher
from shared.database import save_research_history, save_validation_history

logger = logging.getLogger("a2a.coordinator.orchestrator")


class CoordinatorOrchestrator:
    """Orchestrează rularea secvențială sau în lanț a agenților în cadrul fluxurilor de execuție A2A."""

    async def execute_workflow(self, payload: Dict[str, Any], priority: int = 3) -> Dict[str, Any]:
        """Execută fluxul clasic de Rezumare și Traducere (Orchestrare)."""
        text = payload.get("text")
        target_language = payload.get("target_language")

        if not text:
            raise ValueError("Payload-ul nu conține câmpul obligatoriu 'text'.")
        if not target_language:
            raise ValueError("Payload-ul nu conține câmpul obligatoriu 'target_language'.")

        logger.info("Inițializare flux de execuție multi-agent.")
        start_time = time.perf_counter()

        # Faza 1: Rezumare document
        logger.info("Execuție Faza 1: Rezumare text de intrare")
        summarizer_resp = await call_summarizer(text=text, priority=priority)

        if summarizer_resp.status == "failed":
            raise RuntimeError(f"Agentul de Rezumare a eșuat: {summarizer_resp.error}")

        summary_result = summarizer_resp.result
        if not summary_result:
            raise RuntimeError("Agentul de Rezumare a returnat un rezultat gol.")

        summary = summary_result.get("summary", "")
        key_points = summary_result.get("key_points", [])
        logger.info(f"Faza 1 finalizată. Rezumat generat. Lungime caracter: {len(summary)}")

        # Faza 2: Traducere rezumat
        logger.info(f"Execuție Faza 2: Traducere rezumat în limba {target_language}")
        translator_resp = await call_translator(
            text=summary, target_language=target_language, priority=priority
        )

        if translator_resp.status == "failed":
            raise RuntimeError(f"Agentul de Traducere a eșuat: {translator_resp.error}")

        translation_result = translator_resp.result
        if not translation_result:
            raise RuntimeError("Agentul de Traducere a returnat un rezultat gol.")

        translated_text = translation_result.get("translated_text", "")
        logger.info("Faza 2 finalizată. Traducere generată cu succes.")

        total_time = time.perf_counter() - start_time
        logger.info(f"Fluxul de execuție multi-agent s-a finalizat cu succes în {total_time:.4f}s")

        return {
            "original_character_count": len(text),
            "original_summary": summary,
            "key_points": key_points,
            "translated_text": translated_text,
            "target_language": target_language,
            "summarizer_time": summarizer_resp.processing_time,
            "translator_time": translator_resp.processing_time,
            "total_processing_time": total_time,
        }

    async def execute_research_workflow(self, payload: Dict[str, Any], priority: int = 3) -> Dict[str, Any]:
        """Execută noul flux extins de Cercetare (Coordinator -> ResearchAgent -> ValidatorAgent -> SummarizerAgent -> ExportAgent -> Coordinator)."""
        query = payload.get("query")
        result_type = payload.get("result_type", "Rezumat")

        if not query:
            raise ValueError("Payload-ul nu conține câmpul obligatoriu 'query'.")

        logger.info(f"Inițializare flux extins de cercetare A2A pentru subiectul: '{query}'")
        start_time = time.perf_counter()

        # Apel către Research Agent (care coordonează automat în lanț cu ceilalți agenți din aval)
        researcher_resp = await call_researcher(query=query, result_type=result_type, priority=priority)

        if researcher_resp.status == "failed":
            raise RuntimeError(f"Agentul de Cercetare a eșuat: {researcher_resp.error}")

        res_result = researcher_resp.result
        if not res_result:
            raise RuntimeError("Agentul de Cercetare a returnat un rezultat gol.")

        # Extragere date din lanțul complet de răspunsuri A2A
        title = res_result.get("title", query)
        summary = res_result.get("summary", "")
        key_points = res_result.get("key_points", [])
        report = res_result.get("report", "")
        trust_score = res_result.get("trust_score", 70)
        verified_sources = res_result.get("verified_sources", [])
        rejected_sources = res_result.get("rejected_sources", [])
        
        pdf_filename = res_result.get("pdf_filename")
        docx_filename = res_result.get("docx_filename")
        
        validator_time = res_result.get("validator_time", 0.0)
        summarizer_time = res_result.get("summarizer_time", 0.0)
        exporter_time = res_result.get("exporter_time", 0.0)

        total_time = time.perf_counter() - start_time
        logger.info(f"Fluxul extins de cercetare A2A s-a finalizat cu succes în {total_time:.4f}s")

        # Salvare în SQLite a istoricului cercetării și a validării surselor
        try:
            research_id = save_research_history(
                query=query,
                summary=summary if result_type == "Rezumat" else report[:200] + "...",
                sources_count=len(verified_sources)
            )
            save_validation_history(
                research_id=research_id,
                trust_score=trust_score,
                validated_sources=verified_sources
            )
            logger.info("Istoricul cercetării și validării surselor a fost salvat în baza de date SQLite.")
        except Exception as db_err:
            logger.error(f"Eroare la salvarea istoricului în baza de date: {db_err}")

        return {
            "title": title,
            "summary": summary,
            "key_points": key_points,
            "report": report,
            "result_type": result_type,
            "trust_score": trust_score,
            "verified_sources": verified_sources,
            "rejected_sources": rejected_sources,
            "pdf_filename": pdf_filename,
            "docx_filename": docx_filename,
            "researcher_time": researcher_resp.processing_time - validator_time - summarizer_time - exporter_time,
            "validator_time": validator_time,
            "summarizer_time": summarizer_time,
            "exporter_time": exporter_time,
            "total_processing_time": total_time,
        }
