# ─────────────────────────────────────────────────────────────────────────────
#  Zentra — one-command launcher (Windows / PowerShell)
#  Starts the FastAPI backend (:8000) and the Next.js frontend (:3000).
#  Usage:  .\start.ps1          (Ctrl+C stops both)
# ─────────────────────────────────────────────────────────────────────────────
$ErrorActionPreference = "Stop"

$Root        = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend     = Join-Path $Root "backend"
$Frontend    = Join-Path $Root "frontend"
$Python      = Join-Path $Root ".venv\Scripts\python.exe"
$BackendPort = 8000
$FrontendPort= 3000

function Log  ($m) { Write-Host "[zentra] $m" -ForegroundColor Green }
function Warn ($m) { Write-Host "[warn]   $m" -ForegroundColor Yellow }
function Die  ($m) { Write-Host "[error]  $m" -ForegroundColor Red; exit 1 }

# ── pre-flight ───────────────────────────────────────────────────────────────
if (-not (Test-Path $Python))                      { Die "Python venv missing. Run:  python -m venv .venv ; .\.venv\Scripts\python.exe -m pip install -r requirements.txt" }
if (-not (Test-Path (Join-Path $Frontend "node_modules"))) { Die "node_modules missing. Run:  cd frontend ; npm install" }

try {
  $tags = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 5
  $models = $tags.models | ForEach-Object { $_.name }
  Log ("Ollama is up. Models: " + ($models -join ", "))
} catch {
  Warn "Ollama is not responding on http://localhost:11434 — the chatbot will fail."
  Warn "Start it with:  ollama serve"
}

# ── free the ports ───────────────────────────────────────────────────────────
foreach ($port in @($BackendPort, $FrontendPort)) {
  $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
  foreach ($c in $conns) {
    Warn "Port $port busy (PID $($c.OwningProcess)) — stopping it."
    try { Stop-Process -Id $c.OwningProcess -Force -ErrorAction Stop } catch {}
  }
}

# ── backend ──────────────────────────────────────────────────────────────────
Log "Starting backend  -> http://localhost:$BackendPort"
$backendProc = Start-Process -FilePath $Python `
  -ArgumentList @("-m","uvicorn","main:app","--host","0.0.0.0","--port","$BackendPort") `
  -WorkingDirectory $Backend -NoNewWindow -PassThru

# first boot embeds the whole catalogue, so allow generous time
Log "Waiting for backend (first run builds the vector store, this can take a few minutes)..."
$ready = $false
for ($i = 0; $i -lt 180; $i++) {
  Start-Sleep -Seconds 2
  try {
    Invoke-WebRequest -Uri "http://localhost:$BackendPort/api/health" -TimeoutSec 3 -UseBasicParsing | Out-Null
    $ready = $true; break
  } catch {}
}
if (-not $ready) { Die "Backend did not come up. Check the output above." }
Log "Backend ready."

# ── frontend ─────────────────────────────────────────────────────────────────
Log "Starting frontend -> http://localhost:$FrontendPort"
$frontendProc = Start-Process -FilePath "cmd.exe" `
  -ArgumentList @("/c","npm run dev") `
  -WorkingDirectory $Frontend -NoNewWindow -PassThru

for ($i = 0; $i -lt 45; $i++) {
  Start-Sleep -Seconds 2
  try { Invoke-WebRequest -Uri "http://localhost:$FrontendPort" -TimeoutSec 3 -UseBasicParsing | Out-Null; break } catch {}
}

Write-Host ""
Write-Host "──────────────────────────────────────────────" -ForegroundColor Cyan
Write-Host "  Zentra is running" -ForegroundColor Cyan
Write-Host "  Store     ->  http://localhost:$FrontendPort"
Write-Host "  API       ->  http://localhost:$BackendPort"
Write-Host "  API docs  ->  http://localhost:$BackendPort/docs"
Write-Host "──────────────────────────────────────────────" -ForegroundColor Cyan
Write-Host "  Press Ctrl+C to stop both servers"
Write-Host ""

try {
  while ($true) { Start-Sleep -Seconds 1 }
} finally {
  Log "Stopping servers..."
  foreach ($p in @($backendProc, $frontendProc)) {
    if ($p -and -not $p.HasExited) { try { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue } catch {} }
  }
  foreach ($port in @($BackendPort, $FrontendPort)) {
    Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
      ForEach-Object { try { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } catch {} }
  }
  Log "Done."
}
