# ResearchDraft.ai

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![LaTeX](https://img.shields.io/badge/Export-LaTeX%20%2B%20PDF-008080)](https://www.latex-project.org/)
[![Zotero](https://img.shields.io/badge/Literature-Zotero-CC2936)](https://www.zotero.org/)
[![Local First](https://img.shields.io/badge/Mode-Local--First-2E7D32)](#why-researchdraftai)

English | [中文说明](README.zh-CN.md)

ResearchDraft.ai turns a research idea, data description, and curated literature sources into an auditable, editable, and compilable draft package.

It is not an AI paper ghostwriter. The goal is to help researchers organize early-stage writing materials into a traceable manuscript scaffold: Markdown, LaTeX, BibTeX, PDF, literature summaries, and a quality report that can be inspected and revised by humans.

## Why ResearchDraft.ai

Research writing usually starts with scattered inputs: an idea, data notes, Zotero folders, public dataset links, method sketches, and target journal expectations. ResearchDraft.ai connects these inputs into one local workflow so that each generated draft remains reviewable instead of being a black-box AI answer.

The current MVP is designed for researchers who care about:

- data-aware draft generation from both idea and data description;
- Zotero collection-based literature control;
- optional external scholarly search when local references are insufficient;
- citation traceability through BibTeX and LaTeX citation keys;
- PDF preview for manual review;
- local-first execution before any hosted or commercial deployment.

## Core Features

- Import references from a selected Zotero collection.
- Supplement references through external scholarly search when needed.
- Generate English research draft packages for scientific manuscript planning.
- Export Markdown, LaTeX, BibTeX, and compiled PDF files.
- Generate per-paper HTML literature summaries.
- Create a quality report for section alignment, citation/BibTeX consistency, URL handling, math hygiene, and PDF generation.
- Run as a static frontend plus a local Flask backend.

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

## Requirements

- Windows PowerShell
- Python 3.10+
- Optional but recommended: MiKTeX or TeX Live for PDF compilation
- Optional: Node.js for frontend syntax checks
- Optional: Zotero account and API key for collection-based literature import

## One-Command Local Setup

```powershell
git clone https://github.com/xiejhhhhhh/ResearchDraft.ai.git
cd ResearchDraft.ai
.\scripts\setup_local.ps1
```

The setup script creates a virtual environment, installs Python dependencies, prepares the local `.env` template when needed, and runs basic backend checks.

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
2. Choose a literature source:
   - a Zotero collection, or
   - external scholarly search.
3. Enter the research idea, research field or aim, data description, target journal, and output format.
4. Submit the form.
5. Review and download the generated package:
   - `.md`
   - `.tex`
   - `.bib`
   - `.pdf`
   - literature HTML summaries
   - quality report JSON

Generated files are saved locally under:

```text
research_paper_agent\data\
```

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

## Product Direction

The current release is a local MVP for single-user research drafting. It is intended to prove the workflow before moving toward a hosted commercial product.

Future hosted versions should focus on researcher trust and production usability:

- account login and project-level user isolation;
- authenticated downloads and API rate limiting;
- usage and cost tracking for AI and literature retrieval;
- user-controlled data deletion and retention settings;
- SSRF protection for external URLs and file retrieval;
- prompt-injection defenses when processing uploaded or retrieved text;
- a guided setup page for AI keys, Zotero, LaTeX, and PDF compilation;
- a Trust Dashboard for citation traceability, AI disclosure, source provenance, and quality checks.

Research users are sensitive to different concerns in different markets. European and North American users often prioritize data privacy, citation traceability, and AI disclosure. Chinese users often care more about availability, Chinese-language cost, Zotero convenience, and local deployment. ResearchDraft.ai should support both by keeping the local workflow transparent while preparing a safer hosted experience.

## Intended Use

ResearchDraft.ai is best used as a research planning and drafting assistant. It helps convert structured inputs into a draft package that researchers can inspect, correct, cite, compile, and rewrite. It does not replace expert judgment, domain validation, experiment design, authorship responsibility, or journal compliance review.
