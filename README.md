# ResearchDraft.ai

[中文说明](README.zh-CN.md) | English

ResearchDraft.ai is a local-first research drafting workflow for turning a research idea, data description, and curated literature sources into an auditable manuscript package.

It is designed for researchers who want AI assistance without losing control of references, LaTeX files, BibTeX entries, PDF compilation, and quality checks.

## Highlights

- Zotero collection import for project-specific references.
- External scholarly metadata supplementation when local references are insufficient.
- English publishable-paper-oriented draft generation.
- Markdown, LaTeX, BibTeX, and PDF export.
- Per-paper HTML literature summaries.
- Quality reports for section alignment, citation/BibTeX consistency, URL handling, math hygiene, and PDF generation.
- Static frontend plus local Flask backend.

## Repository Layout

```text
docs/                         Static frontend and documentation pages
research_paper_agent/         Flask backend and research-draft engine
research_paper_agent/export/  BibTeX, LaTeX text helpers, and PDF compilation
research_paper_agent/literature/
                              Zotero, external search, and reference weighting
research_paper_agent/generation/
                              Prompt construction
research_paper_agent/validation/
                              Quality gate
scripts/                      Local setup, startup, checks, and structure docs
PROJECT_SUMMARY.md            Project handoff notes
```

Open `docs/code_structure.html` for a generated map of the Python module structure.

## One-Command Local Setup

Requirements:

- Windows PowerShell
- Python 3.10+
- Optional but recommended: MiKTeX or TeX Live for PDF generation

Run:

```powershell
git clone https://github.com/xiejhhhhhh/ResearchDraft.ai.git
cd ResearchDraft.ai
.\scripts\setup_local.ps1
```

The setup script will:

- create `.venv`;
- install Python dependencies;
- copy `research_paper_agent\.env.example` to `research_paper_agent\.env` if needed;
- run backend unit checks.

Then edit:

```text
research_paper_agent\.env
```

Configure at least one AI provider. For Zotero mode, also configure Zotero:

```text
VOLCENGINE_API_KEY=your_key_here
VOLCENGINE_MODEL_ID=your_model_or_endpoint_id
ZOTERO_LIBRARY_ID=your_zotero_library_id
ZOTERO_API_KEY=your_zotero_api_key
ZOTERO_LIBRARY_TYPE=user
```

Do not commit `.env`.

## Start the App

Terminal 1:

```powershell
.\scripts\start_backend.ps1
```

Terminal 2:

```powershell
.\scripts\start_frontend.ps1
```

Open:

```text
http://127.0.0.1:8000
```

Backend health check:

```text
http://127.0.0.1:9000/api/status
```

Zotero collections:

```text
http://127.0.0.1:9000/api/zotero/collections
```

## Basic Usage

1. Start the backend and frontend.
2. Select a literature source:
   - Zotero collection, or
   - external scholarly search.
3. Enter:
   - research idea;
   - research field or aim;
   - data description;
   - target journal, if available;
   - output format, usually `tex`.
4. Submit the form.
5. Download generated files:
   - `.md`
   - `.tex`
   - `.bib`
   - `.pdf`
   - literature HTML summaries
   - quality report JSON

Generated artifacts are saved under:

```text
research_paper_agent\data\
```

This folder is ignored by git.

## Run Checks

```powershell
.\scripts\run_checks.ps1
```

Manual backend checks:

```powershell
cd research_paper_agent
python -m py_compile service.py api.py models.py literature\external_search.py literature\zotero.py literature\ranking.py generation\prompts.py export\bibtex.py export\latex_text.py export\pdf.py validation\quality_gate.py
python -m unittest tests.test_quality_gate tests.test_export_helpers tests.test_literature_and_prompts
```

Frontend syntax check, if Node.js is installed:

```powershell
cd docs
node --check app.js
```

## Security

Never commit:

- `research_paper_agent/.env`
- generated drafts, PDFs, BibTeX files, and literature summaries
- `research_paper_agent/data/submissions.json`
- cache files
- local tools under `.tools/`

The repository includes `.gitignore` rules for these paths.

## Current MVP Boundary

MVP2 is a local, single-user research drafting workflow. It is not yet a hosted multi-user SaaS product.

Before commercial hosting, add:

- authentication;
- per-user project isolation;
- signed downloads;
- rate limiting;
- task queues;
- cloud storage policy;
- audit logs;
- privacy and data-retention controls.

