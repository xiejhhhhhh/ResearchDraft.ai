# ResearchDraft.ai

ResearchDraft.ai is a local-first MVP for generating auditable research-draft packages from a research idea, data description, and literature sources.

The current MVP2 workflow can:

- read references from a selected Zotero collection;
- supplement references through external scholarly metadata search when needed;
- generate an English publishable-paper-oriented outline;
- export Markdown, LaTeX, BibTeX, and PDF review files;
- generate per-paper HTML summaries;
- run a quality gate for section alignment, BibTeX/citation consistency, URL handling, math hygiene, and PDF generation.

## Repository Structure

```text
docs/                     Static frontend and project structure pages
research_paper_agent/     Flask backend and local generation engine
scripts/                  Helper scripts, including code-structure HTML generation
PROJECT_SUMMARY.md        Current project handoff notes
```

Important backend modules:

```text
research_paper_agent/literature/      Zotero, external search, and citation weighting
research_paper_agent/export/          BibTeX, LaTeX text helpers, and PDF compilation
research_paper_agent/generation/      Prompt construction
research_paper_agent/validation/      Quality gate
```

Open `docs/code_structure.html` for a generated map of the current Python module layout.

## Local Setup

```powershell
cd research_paper_agent
python -m pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` locally. Do not commit `.env`.

At minimum, configure one AI provider and, for Zotero mode, Zotero credentials:

```text
VOLCENGINE_API_KEY=your_key_here
VOLCENGINE_MODEL_ID=your_endpoint_or_model_id
ZOTERO_LIBRARY_ID=your_zotero_library_id
ZOTERO_API_KEY=your_zotero_api_key
ZOTERO_LIBRARY_TYPE=user
```

## Run Locally

Backend:

```powershell
cd research_paper_agent
python api.py
```

Frontend:

```powershell
cd docs
python -m http.server 8000
```

Open:

```text
http://127.0.0.1:8000
```

## Tests

```powershell
cd research_paper_agent
python -m py_compile service.py api.py models.py literature\external_search.py literature\zotero.py literature\ranking.py generation\prompts.py export\bibtex.py export\latex_text.py export\pdf.py validation\quality_gate.py
python -m unittest tests.test_quality_gate tests.test_export_helpers tests.test_literature_and_prompts
```

If Node.js is installed, check the frontend:

```powershell
cd docs
node --check app.js
```

## Security Notes

Never commit:

- `.env`
- generated drafts, PDFs, BibTeX files, or literature summaries;
- `data/submissions.json`;
- cache files;
- personal Zotero exports or private research proposals.

Generated user artifacts are intentionally ignored by `.gitignore`.

