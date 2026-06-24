# Script PowerShell pentru pornirea automată a tuturor agenților A2A în ferestre separate.
# Autori: Fălcoi Ionuț Marian și Dincă Andrei

$ErrorActionPreference = "Stop"

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "   Pornire Sistem Multi-Agent A2A (Fălcoi Ionuț & Dincă Andrei)  " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

# Verificare existență mediu virtual (venv)
if (Test-Path ".\venv") {
    Write-Host "[Info] Se utilizează mediul virtual detectat (venv)." -ForegroundColor Green
    $pythonCmd = ".\venv\Scripts\python.exe"
} else {
    Write-Host "[Avertisment] Mediul virtual 'venv' nu a fost găsit în directorul curent." -ForegroundColor Yellow
    Write-Host "Se va folosi interpretorul global 'python'. Asigurați-vă că dependențele sunt instalate." -ForegroundColor Yellow
    $pythonCmd = "python"
}

# Definiție agenți
$agents = @(
    @{ Name = "Agent Rezumare (Summarizer)"; Module = "summarizer.main"; Port = 8001 },
    @{ Name = "Agent Traducere (Translator)"; Module = "translator.main"; Port = 8002 },
    @{ Name = "Agent Cercetare (Researcher)"; Module = "researcher.main"; Port = 8003 },
    @{ Name = "Agent Validare Surse (Validator)"; Module = "validator.main"; Port = 8004 },
    @{ Name = "Agent Export (Exporter)"; Module = "exporter.main"; Port = 8005 },
    @{ Name = "Agent Coordonator (Coordinator)"; Module = "coordinator.main"; Port = 8000 }
)

# Pornire agenți în ferestre separate
foreach ($agent in $agents) {
    Write-Host "Se inițializează $($agent.Name) pe portul $($agent.Port)..." -ForegroundColor Gray
    
    # Lansează procesul într-o nouă fereastră de terminal cu titlul setat corespunzător
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle = '$($agent.Name)'; & $pythonCmd -m $($agent.Module)"
    
    # Mică pauză pentru a asigura pornirea secvențială ordonată
    Start-Sleep -Milliseconds 700
}

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host " Toți agenții au fost lansați cu succes în ferestre separate!" -ForegroundColor Green
Write-Host " Deschideți browser-ul la adresa:" -ForegroundColor White
Write-Host " 👉 http://127.0.0.1:8000/" -ForegroundColor Green -NoNewline
Write-Host " (Dashboard Coordonator)" -ForegroundColor White
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host " Notă: Pentru a opri sistemul, închideți ferestrele de terminal pornite." -ForegroundColor Yellow
