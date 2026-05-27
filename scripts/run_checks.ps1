$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Backend = Join-Path $Root "research_paper_agent"
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$Python = if (Test-Path $VenvPython) { $VenvPython } else { "python" }

Push-Location $Backend
try {
    & $Python -m py_compile service.py api.py models.py literature\external_search.py literature\zotero.py literature\ranking.py generation\prompts.py export\bibtex.py export\latex_text.py export\pdf.py validation\quality_gate.py
    & $Python -m unittest tests.test_quality_gate tests.test_export_helpers tests.test_literature_and_prompts
}
finally {
    Pop-Location
}

$NodeCandidates = @(
    (Join-Path $Root ".tools\node\node.exe"),
    "node"
)

foreach ($Candidate in $NodeCandidates) {
    try {
        & $Candidate --version *> $null
        Push-Location (Join-Path $Root "docs")
        try {
            & $Candidate --check app.js
        }
        finally {
            Pop-Location
        }
        break
    }
    catch {
        continue
    }
}

Write-Host "Checks complete."

