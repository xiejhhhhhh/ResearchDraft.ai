param(
    [switch]$SkipChecks
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Backend = Join-Path $Root "research_paper_agent"
$Venv = Join-Path $Root ".venv"

Write-Host "ResearchDraft.ai local setup"
Write-Host "Project root: $Root"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python was not found in PATH. Install Python 3.10+ first."
}

if (-not (Test-Path $Venv)) {
    python -m venv $Venv
}

$Python = Join-Path $Venv "Scripts\python.exe"
& $Python -m pip install --upgrade pip
& $Python -m pip install -r (Join-Path $Backend "requirements.txt")

$EnvFile = Join-Path $Backend ".env"
$EnvExample = Join-Path $Backend ".env.example"
if (-not (Test-Path $EnvFile) -and (Test-Path $EnvExample)) {
    Copy-Item -LiteralPath $EnvExample -Destination $EnvFile
    Write-Host "Created research_paper_agent\.env from .env.example. Edit it before real generation."
}

if (-not $SkipChecks) {
    Push-Location $Backend
    try {
        & $Python -m py_compile service.py api.py models.py literature\external_search.py literature\zotero.py literature\ranking.py generation\prompts.py export\bibtex.py export\latex_text.py export\pdf.py validation\quality_gate.py
        & $Python -m unittest tests.test_quality_gate tests.test_export_helpers tests.test_literature_and_prompts
    }
    finally {
        Pop-Location
    }
}

Write-Host ""
Write-Host "Setup complete."
Write-Host "Next:"
Write-Host "  1. Edit research_paper_agent\.env"
Write-Host "  2. Start backend:  .\scripts\start_backend.ps1"
Write-Host "  3. Start frontend: .\scripts\start_frontend.ps1"

