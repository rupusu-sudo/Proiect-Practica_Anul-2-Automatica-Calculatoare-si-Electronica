# pyrefly: ignore [missing-import]
import httpx
import io
import sys
import time

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

COORDINATOR_URL = "http://127.0.0.1:8000"

DEMO_TEXT = (
    "Inteligența Artificială (IA) transformă dezvoltarea software într-un ritm fără precedent. "
    "Prin integrarea sistemelor multi-agent moderne, sarcini complexe care înainte necesitau intervenție "
    "umană manuală—precum rezumarea codului, traducerea limbajelor, rutarea API-urilor și sinteza codului—sunt "
    "acum automatizate. Acești agenți operează în mod autonom, comunicând prin protocoale standardizate "
    "precum protocolul personalizat A2A (Agent-to-Agent). Folosind topologii bazate pe microservicii, studenții "
    "pot construi și evalua agenți IA independenți care rulează local. Acest flux colaborativ arată cum agenții "
    "specializați, precum un Rezumator și un Traducător, pot fi coordonați pentru a livra rezultate "
    "valoroase cu latență de rețea redusă și fiabilitate ridicată."
)


async def run_demo():
    print("=================================================================")
    print("      CLIENT DEMO — SISTEM MULTI-AGENT CU PROTOCOL A2A")
    print("=================================================================\n")

    async with httpx.AsyncClient(timeout=45.0) as client:
        print("[Pasul 1] Verificare stare de sănătate Agent Coordonator...")
        try:
            resp = await client.post(f"{COORDINATOR_URL}/health")
            if resp.status_code == 200:
                print(f"Stare: OK | Răspuns: {resp.json()}\n")
            else:
                print(f"Verificarea stării a eșuat cu codul: {resp.status_code}\n")
                return
        except httpx.ConnectError:
            print(f"Eroare: Nu s-a putut stabili conexiunea cu Agentul Coordonator la {COORDINATOR_URL}.")
            print("Asigurați-vă că toate cele 3 microservicii sunt pornite (porturile 8000, 8001, 8002).\n")
            return

        print("[Pasul 2] Interogare metadate info Agent Coordonator...")
        resp = await client.get(f"{COORDINATOR_URL}/info")
        print(f"Info Agent: {resp.json()}\n")

        print("[Pasul 3] Trimitere cerere de orchestrare către Coordonator...")
        print(f"Conținut payload trimis: '{DEMO_TEXT[:100]}...'\n")

        payload = {"text": DEMO_TEXT, "target_language": "Romanian", "priority": 3}
        start_time = time.perf_counter()
        response = await client.post(f"{COORDINATOR_URL}/orchestrate", json=payload)
        end_time = time.perf_counter()

    if response.status_code == 200:
        data = response.json()
        result = data.get("result", {})
        print("===================== RĂSPUNS ORCHESTRARE =====================")
        print(f"ID Mesaj:   {data.get('message_id')}")
        print(f"Stare:      {data.get('status').upper()}")
        print(f"Durată:     {data.get('processing_time'):.4f} secunde")
        print("-----------------------------------------------------------------")
        print(f"Rezumat Original:\n{result.get('original_summary')}\n")
        print("Puncte Cheie:")
        for point in result.get("key_points", []):
            print(f"  - {point}")
        print()
        print(f"Rezumat Tradus (Limba: {result.get('target_language')}):")
        print(f"{result.get('translated_text')}\n")
        print("Metrici Diagnostice Flux:")
        print(f"  * Timp Rezumator: {result.get('summarizer_time', 0):.4f}s")
        print(f"  * Timp Traducător: {result.get('translator_time', 0):.4f}s")
        print(f"  * Timp Coordonator total: {end_time - start_time:.4f}s")
        print("=================================================================")
    else:
        print(f"Cererea a eșuat cu codul de stare: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_demo())
