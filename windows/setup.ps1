# One-time setup on Windows. In PowerShell, from the project folder:
#   Set-ExecutionPolicy -Scope Process Bypass
#   .\windows\setup.ps1                 # core + control panel
#   .\windows\setup.ps1 -WithLangChain  # also the LangChain / LangGraph version
param([switch]$WithLangChain, [switch]$SkipTests, [switch]$SkipOllama)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host "== 1/6 Python" -ForegroundColor Cyan
$py = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $ErrorActionPreference = "Continue"           # "py -3.10" on a missing version writes to stderr; that is not fatal here
    foreach ($v in "3.11", "3.12", "3.13", "3.10") {
        & py "-$v" -c "import sys" 2>$null
        if ($LASTEXITCODE -eq 0) { $py = $v; break }
    }
    $ErrorActionPreference = "Stop"
}
if (-not $py) {
    Write-Host "Python 3.10-3.13 not found. Install Python 3.11 from https://www.python.org/downloads/windows/ (tick 'Add python.exe to PATH'), then run this again." -ForegroundColor Red
    exit 1
}
Write-Host "using Python $py"

Write-Host "== 2/6 virtual environment (.venv)" -ForegroundColor Cyan
if (-not (Test-Path .venv\Scripts\python.exe)) { & py "-$py" -m venv .venv }
$vpy = (Resolve-Path .venv\Scripts\python.exe).Path
& $vpy -m pip install --upgrade pip --quiet

Write-Host "== 3/6 packages (a few minutes the first time; sentence-transformers pulls PyTorch)" -ForegroundColor Cyan
& $vpy -m pip install -r requirements.txt -r requirements-panel.txt -r requirements-serve.txt
if ($WithLangChain) { & $vpy -m pip install -r requirements-lc.txt }
& $vpy -m pip install -e . --quiet

Write-Host "== 4/6 .env" -ForegroundColor Cyan
if (-not (Test-Path .env)) { Copy-Item .env.example .env; Write-Host "created .env (put ANTHROPIC_API_KEY there or in the panel)" }

Write-Host "== 5/6 Ollama" -ForegroundColor Cyan
$model = & $vpy -c "from support.settings import load; print(load().llm.chat_model)"
if ($SkipOllama) {
    Write-Host "skipped"
} elseif (Get-Command ollama -ErrorAction SilentlyContinue) {
    ollama pull $model
} else {
    Write-Host "Ollama not found. Install it from https://ollama.com/download/windows, then run: ollama pull $model" -ForegroundColor Yellow
}

Write-Host "== 6/6 tests" -ForegroundColor Cyan
if (-not $SkipTests) { & $vpy -m pytest -q }

Write-Host ""
Write-Host "Done. Start the panel:            windows\start_panel.bat" -ForegroundColor Green
Write-Host "Connect Claude Desktop (optional): windows\install_claude_desktop.bat  (then quit and reopen Claude Desktop)" -ForegroundColor Green
