# ResearchDraft.ai Workspace Notes

## Default Workspace

- Backend code lives in `research_paper_agent/`.
- Frontend static files live in `docs/`.
- Generated drafts, BibTeX files, PDFs, literature summaries, caches, and submitted metadata should stay under `research_paper_agent/data/`.

## Local Commands

Start backend:

```powershell
cd research_paper_agent
python api.py
```

Start frontend:

```powershell
cd docs
python -m http.server 8000
```

Check backend:

```powershell
Invoke-WebRequest -Uri http://127.0.0.1:9000/api/status -UseBasicParsing
```

## Secret Safety

- `research_paper_agent/.env` contains local API credentials and must not be uploaded.
- Keep `.env.example` and `.env.template` as placeholder-only files.
