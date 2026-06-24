import sqlite3
import os
import json
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "a2a_database.db")


def init_db():
    """Inițializează baza de date SQLite și creează tabelele necesare."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Istoric cercetare generală
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS research_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            summary TEXT NOT NULL,
            sources_count INTEGER NOT NULL
        )
    """)
    
    # Istoric validare surse (nou)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS source_validation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            research_id INTEGER,
            trust_score INTEGER NOT NULL,
            validated_sources TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    
    # Istoric exporturi (nou, pentru metrica de Documente Generate)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS export_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            format TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()


def save_research_history(query: str, summary: str, sources_count: int) -> int:
    """Salvează cercetarea și returnează ID-ul rândului generat."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp_str = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        "INSERT INTO research_history (query, timestamp, summary, sources_count) VALUES (?, ?, ?, ?)",
        (query, timestamp_str, summary, sources_count)
    )
    last_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_id


def save_validation_history(research_id: int, trust_score: int, validated_sources: list):
    """Salvează detaliile validării surselor."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp_str = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        "INSERT INTO source_validation_history (research_id, trust_score, validated_sources, timestamp) VALUES (?, ?, ?, ?)",
        (research_id, trust_score, json.dumps(validated_sources), timestamp_str)
    )
    conn.commit()
    conn.close()


def save_export_event(file_format: str):
    """Înregistrează un eveniment de export document."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp_str = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        "INSERT INTO export_history (format, timestamp) VALUES (?, ?)",
        (file_format, timestamp_str)
    )
    conn.commit()
    conn.close()


def get_all_research_history():
    """Returnează istoricul de cercetare."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, query, timestamp, summary, sources_count FROM research_history ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": row[0],
            "query": row[1],
            "timestamp": row[2],
            "summary": row[3],
            "sources_count": row[4]
        }
        for row in rows
    ]


def get_system_metrics():
    """Calculează metricile de sistem solicitate."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Average Trust Score
    cursor.execute("SELECT AVG(trust_score) FROM source_validation_history")
    avg_score_row = cursor.fetchone()
    avg_score = round(avg_score_row[0]) if avg_score_row and avg_score_row[0] is not None else 0
    
    # 2. Generated Documents
    cursor.execute("SELECT COUNT(*) FROM export_history")
    gen_docs_row = cursor.fetchone()
    gen_docs = gen_docs_row[0] if gen_docs_row else 0
    
    # 3. Validated Sources (Numărul total de surse unice sau numărate înregistrări)
    cursor.execute("SELECT validated_sources FROM source_validation_history")
    rows = cursor.fetchall()
    validated_sources_count = 0
    for row in rows:
        try:
            sources_list = json.loads(row[0])
            validated_sources_count += len(sources_list)
        except Exception:
            pass
            
    conn.close()
    
    return {
        "avg_trust_score": avg_score,
        "generated_documents": gen_docs,
        "validated_sources": validated_sources_count
    }
