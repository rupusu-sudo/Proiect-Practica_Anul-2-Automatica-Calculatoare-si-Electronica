import logging
from typing import Dict, Any, List

logger = logging.getLogger("a2a.validator")

HIGH_TRUST_KEYWORDS = [
    ".edu", ".gov", "britannica.com", "ieee.org", "acm.org", "nature.com",
    "science.org", "sciencedirect.com", "wikipedia.org", "scholar.google"
]

LOW_TRUST_KEYWORDS = [
    "blog", "forum", "reddit.com", "wordpress", "blogspot", "medium.com",
    "quora.com", "tumblr.com", "twitter.com", "facebook.com", "github.com/community"
]


class SourceValidatorProcessor:
    """Validează credibilitatea surselor culese în cadrul fluxului de cercetare."""

    def process_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        sources = payload.get("sources", [])
        if not sources:
            # Dacă nu avem surse, returnăm un scor implicit
            return {
                "trust_score": 70,
                "verified_sources": ["https://scholar.google.com (implicit)"],
                "rejected_sources": []
            }

        # 1. Eliminare duplicate păstrând ordinea
        unique_sources = []
        for src in sources:
            src_str = str(src).strip()
            if src_str and src_str not in unique_sources:
                unique_sources.append(src_str)

        verified_sources = []
        rejected_sources = []
        total_score = 0

        # 2. Analiză granulară pentru fiecare sursă
        for src in unique_sources:
            src_lower = src.lower()
            source_score = 70  # Scor de bază neutru

            # Verificare cuvinte cheie de încredere mare
            if any(kw in src_lower for kw in HIGH_TRUST_KEYWORDS):
                source_score = 95
                verified_sources.append(src)
            # Verificare cuvinte cheie de încredere scăzută
            elif any(kw in src_lower for kw in LOW_TRUST_KEYWORDS):
                source_score = 40
                rejected_sources.append(src)
            else:
                # Scor mediu pentru alte domenii
                source_score = 65
                verified_sources.append(src)

            total_score += source_score

        # Calcul scor mediu general
        avg_score = round(total_score / len(unique_sources)) if unique_sources else 70
        avg_score = max(0, min(100, avg_score))

        logger.info(f"Validare finalizată. Trust Score: {avg_score} | Verificate: {len(verified_sources)} | Respinse: {len(rejected_sources)}")

        return {
            "trust_score": avg_score,
            "verified_sources": verified_sources,
            "rejected_sources": rejected_sources
        }
