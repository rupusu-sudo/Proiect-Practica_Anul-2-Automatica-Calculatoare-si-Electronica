# Documentație Proiect de Practică: Sistem Multi-Agent (Protocol A2A)

Proiect realizat pentru evaluarea practică din cadrul cursului de **Sisteme Multi-Agent**.

## 👥 Autori
* **Fălcoi Ionuț Marian**
* **Dincă Andrei**

---

## 📖 1. Introducere și Rolul Proiectului
Acest proiect reprezintă o platformă avansată de cercetare academică, analiză și export de documente, bazată pe o arhitectură descentralizată de tip **Sisteme Multi-Agent**. Sistemul utilizează un protocol personalizat numit **Agent-to-Agent (A2A)** peste HTTP REST pentru a orchestra sarcini complexe prin intermediul a 6 microservicii (agenți software) independente.

Scopul principal este eficientizarea colectării informațiilor, validarea credibilității acestora, sintetizarea într-un format academic riguros și exportul în formate descărcabile (.PDF și .DOCX).

---

## 🏛️ 2. Arhitectura Rețelei Multi-Agent
Sistemul este alcătuit din 6 agenți care rulează pe porturi dedicate:

1. **Agentul Coordonator (`coordinator` - Port 8000)**:
   * **Rol**: Punctul central de intrare al sistemului. Găzduiește dashboard-ul web și API-ul principal.
   * **Funcționalitate**: Primește cererile de la utilizator, determină fluxul de lucru necesar (orchestrare simplă sau cercetare extinsă), trimite sarcinile agenților din aval, colectează rezultatele intermediare și expune rezultatele consolidat.

2. **Agentul de Rezumare (`summarizer` - Port 8001)**:
   * **Rol**: Procesarea limbajului natural (LLM) pentru text.
   * **Funcționalitate**: Utilizează un furnizor LLM (OpenAI API sau Ollama local) pentru a rezuma texte lungi sau rapoarte de cercetare brute și extrage ideile principale. Pentru fluxul de cercetare, trimite datele sintetizate direct către Agentul de Export (înlănțuire A2A).

3. **Agentul de Traducere (`translator` - Port 8002)**:
   * **Rol**: Localizare și traducere lingvistică.
   * **Funcționalitate**: Traduce rezumatele generate din limba originală în limba țintă specificată de utilizator (ex. Română sau Engleză).

4. **Agentul de Cercetare (`researcher` - Port 8003)**:
   * **Rol**: Căutare autonomă de informații.
   * **Funcționalitate**: Caută date în timp real pe internet pe baza unui subiect trimis ca interogare și structurează faptele brute descoperite. După colectare, trimite automat datele către Agentul de Validare.

5. **Agentul de Validare a Surselor (`validator` - Port 8004)**:
   * **Rol**: Filtrare calitativă și evaluare a credibilității.
   * **Funcționalitate**: Analizează link-urile culese de cercetător, elimină duplicatele, evaluează reputația domeniilor web și generează un scor global de încredere (**Trust Score**), separând sursele valide de cele nesigure.

6. **Agentul de Export (`exporter` - Port 8005)**:
   * **Rol**: Generare de documente fizice.
   * **Funcționalitate**: Preia raportul centralizat și generează fișiere formatate academic în formatele **PDF** și **DOCX**, înregistrând exportul în baza de date.

---

## 📬 3. Protocolul de Comunicare A2A (Mesageria)
Toți agenții interacționează folosind modele Pydantic stricte pentru a se asigura că toate datele transmise respectă standardele stabilite:

### Structura Cererii (`A2AMessage`)
* `message_id` (UUIDv4): Identificator unic folosit pentru urmărirea cererii prin toată rețeaua de agenți.
* `sender` & `receiver`: Agenți validați (trebuie să aparțină grupului celor 6 agenți + utilizatorul final).
* `timestamp` (UTC): Data și ora trimiterii.
* `task_type`: Tipul acțiunii (`orchestrate`, `research`, `validate_sources`, `summarize_research`, etc.).
* `priority`: Nivelul de prioritate de la 1 (maximă) la 5 (minimă).
* `payload`: Dicționar flexibil de date specifice fiecărei sarcini (ex: `text`, `query`, `target_language`).

### Structura Răspunsului (`A2AResponse`)
* `message_id`: Se potrivește cu UUID-ul cererii originale.
* `status`: Starea procesării (`completed` sau `failed`).
* `processing_time` (float): Durata execuției în secunde.
* `result`: Dicționar ce conține rezultatele procesării (obligatoriu în caz de succes).
* `error`: Detalii despre excepție (obligatoriu în caz de eșec).

---

## 🗄️ 4. Modelul Bazei de Date (Persistență)
Aplicația folosește o bază de date locală **SQLite** (`a2a_database.db`) cu trei tabele:
1. `research_history`: Salvează subiectul căutat, rezumatul și numărul de surse identificate.
2. `source_validation_history`: Corelează rezultatul cu istoricul validării, reținând scorul de încredere (**Trust Score**) și lista de surse aprobate în format JSON.
3. `export_history`: Monitorizează de câte ori s-au generat documente în formatele PDF sau Word pentru analize de performanță.

---

## 🚀 5. Cum Funcționează și Cum se Pornește Proiectul

### ⚠️ Cerințe Prealabile
1. **Python 3.10+** instalat pe mașină.
2. Un fișier `.env` configurat în rădăcina proiectului cu cheia ta API sau URL-ul local Ollama:
   ```env
   LLM_PROVIDER=openai
   OPENAI_API_KEY=cheia_ta_aici
   OPENAI_MODEL=gpt-4o-mini
   ```

### ⚡ Pornire Automată (Recomandat)
Am creat un script automat în PowerShell care inițializează toți cei 6 agenți în ferestre paralele cu un singur click:
1. Deschideți terminalul în rădăcina proiectului.
2. Rulați comanda:
   ```powershell
   .\start_agents.ps1
   ```
Toate microserviciile vor fi deschise în fundal, iar dashboard-ul va fi accesibil la:
👉 **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

---

## 📂 6. Structura Fișierelor din Proiect
* `coordinator/`: Codul principal al agentului coordonator și interfața sa web (`index.html`).
* `summarizer/`: Logica de rezumare prin LLM-uri.
* `translator/`: Logica pentru traducere.
* `researcher/`: Logica de colectare date web.
* `validator/`: Sistemul de evaluare a scorului de încredere pentru site-uri.
* `exporter/`: Modulul de generare fișiere PDF/DOCX.
* `shared/`: Configurații, modele Pydantic, utilitare și baza de date.
* `tests/`: Suita de teste unitare și de integrare.
* `demo_client.py`: Script de test în consolă pentru interacțiuni rapide.
* `start_agents.ps1`: Scriptul automat de lansare a platformei.
