# Sistem Multi-Agent de Cercetare și Procesare Academică (Protocol A2A)

Proiect realizat pentru evaluarea practică din cadrul cursului de Sisteme Multi-Agent și Inginerie Software Academică.

**Autori:**
* **Fălcoi Ionuț Marian**
* **Dincă Andrei**

Acest proiect reprezintă o platformă completă, robustă și optimizată de cercetare academică și procesare de documente. Sistemul utilizează un protocol personalizat **Agent-to-Agent (A2A)** peste HTTP REST pentru a orchestra sarcini complexe prin intermediul a 6 microservicii (agenți independenți).

---

## 🏛️ Arhitectura Sistemului (Topologie Multi-Agent)

Sistemul este compus din următorii agenți software independenți, fiecare rulând pe un port dedicat:

1. **Agent Coordonator (`coordinator` - Port 8000)**: Punctul de acces principal. Primește cererile de la client, structurează mesajele conform protocolului A2A, determină fluxul de execuție, direcționează sarcinile către agenții corespunzători, centralizează rezultatele intermediare și returnează rezultatul final consolidat.
2. **Agent de Cercetare (`researcher` - Port 8003)**: Caută informații în timp real despre concepte, personalități istorice, tehnologii, companii sau subiecte academice, structurând rezultatele brute colectate din diverse surse web.
3. **Agent de Validare a Surselor (`validator` - Port 8004)**: Inspectează credibilitatea surselor culese de cercetător. Elimină duplicatele, evaluează reputația domeniilor și acordă un scor global de încredere (**Trust Score**), separând sursele valide de cele nesigure.
4. **Agent de Rezumare (`summarizer` - Port 8001)**: Primește textul brut sau sursele validate și utilizează un model LLM (OpenAI sau Ollama local) pentru a sintetiza informațiile într-un rezumat academic detaliat și o listă cu idei principale.
5. **Agent de Traducere (`translator` - Port 8002)**: Traduce rezumatul academic în limba țintă specificată de utilizator (Română sau Engleză).
6. **Agent de Export (`exporter` - Port 8005)**: Preia documentul academic consolidat (titlu, rezumat, idei cheie, surse validate, scor de încredere) și generează fișiere pre-formatate în format **PDF** și **DOCX** gata de descărcare.

---

## 📬 Protocolul de Comunicare A2A (Schema Mesajelor)

Toți agenții din rețea comunică folosind modele Pydantic standardizate pentru a garanta interoperabilitatea.

### Structură Mesaj Cerere (`A2AMessage`)
```json
{
  "message_id": "UUIDv4 unic pentru urmărire/tracing",
  "sender": "coordinator | researcher | validator | summarizer | translator | exporter | user",
  "receiver": "coordinator | researcher | validator | summarizer | translator | exporter | user",
  "timestamp": "Timestamp UTC în format ISO 8601",
  "task_type": "orchestrate | research | validate | summarize | translate | export",
  "priority": "Prioritate sarcină: 1 (Maximă) la 5 (Minimă)",
  "payload": {
    "query": "Termenul de căutat (opțional)",
    "text": "Textul de procesat/tradus/rezumat (opțional)",
    "target_language": "Limba țintă: 'Română' sau 'Engleză'",
    "result_type": "Tip output: 'Rezumat' sau 'Raport'"
  }
}
```

### Structură Răspuns (`A2AResponse`)
```json
{
  "message_id": "UUID-ul corespunzător cererii",
  "status": "completed | failed",
  "processing_time": 1.245,
  "result": {
    "summary": "Rezumatul academic...",
    "key_points": ["Punctul 1", "Punctul 2"],
    "trust_score": 85,
    "verified_sources": ["https://..."],
    "rejected_sources": ["http://..."],
    "pdf_filename": "raport_XXXX.pdf",
    "docx_filename": "raport_XXXX.docx"
  },
  "error": "Descrierea erorii în caz de eșec (altfel null)"
}
```

---

## 🗄️ Persistență Date (SQLite)

Platforma stochează istoricul rulărilor academice în baza de date locală `a2a_database.db` folosind următoarele tabele:
- `research_history`: Salvează titlul, rezumatul, punctele cheie și timpii de procesare pentru fiecare cercetare finalizată cu succes.
- `source_validation_history`: Înregistrează scorul de încredere (Trust Score), sursele verificate și sursele respinse.
- `export_history`: Contorizează descărcările de documente generate de către utilizatori, segmentat pe format (.pdf, .docx).

---

## 🛠️ Instalare și Configurare

### Cerințe minime
* Python 3.10 sau mai nou
* Conexiune la internet sau o instanță locală Ollama pornită

### Pasul 1: Clonarea și pregătirea spațiului
```bash
git clone https://github.com/utilizator/proiect-a2a.git
cd proiect-a2a
```

### Pasul 2: Crearea și activarea mediului virtual
```bash
# Pe Windows (PowerShell):
python -m venv venv
.\venv\Scripts\Activate.ps1

# Pe macOS/Linux:
python3 -m venv venv
source venv/bin/activate
```

### Pasul 3: Instalarea dependențelor
```bash
pip install -r requirements.txt
```

### Pasul 4: Configurarea variabilelor de mediu
Creați un fișier numit `.env` în rădăcina proiectului:

**Pentru OpenAI (Implicit)**:
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=cheia-ta-api-openai
OPENAI_MODEL=gpt-4o-mini
```

**Pentru rulare locală (Ollama)**:
```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

---

## 🚀 Pornirea Agenților în Rețea

Pentru a porni întreaga topologie de microservicii, rulați fișierele corespunzătoare în terminale separate (asigurați-vă că mediul virtual `venv` este activat):

```bash
# Terminal 1: Agent Rezumare
python -m summarizer.main

# Terminal 2: Agent Traducere
python -m translator.main

# Terminal 3: Agent Cercetare
python -m researcher.main

# Terminal 4: Agent Validare Surse
python -m validator.main

# Terminal 5: Agent Export
python -m exporter.main

# Terminal 6: Agent Coordonator (și Dashboard-ul Web)
python -m coordinator.main
```

Odată porniți toți agenții, accesați panoul web de control la adresa:
👉 **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

---

## 🧪 Rularea Testelor Automate

Pentru a valida integritatea rețelei A2A și corectitudinea formatelor de mesaje, rulați suita de teste unitare și de integrare:

```bash
pytest -v
```

Pentru a genera raportul de acoperire a codului (coverage):
```bash
pytest --cov=coordinator --cov=summarizer --cov=translator --cov=researcher --cov=validator --cov=exporter --cov=shared tests/
```
