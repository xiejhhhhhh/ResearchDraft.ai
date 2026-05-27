# ResearchDraft.ai Workspace Notes

This project has been moved to `D:\DraftAI_agent`.

## Default Workspace

- Use `D:\DraftAI_agent` as the default project root.
- Backend code lives in `D:\DraftAI_agent\research_paper_agent`.
- Frontend static files live in `D:\DraftAI_agent\docs`.
- Generated drafts, BibTeX files, PDFs, literature summaries, caches, and submitted metadata should stay under `D:\DraftAI_agent\research_paper_agent\data`.
- Do not create new ResearchDraft.ai code, downloads, or generated program files under `C:\Python_code`.
- If a new project subfolder is needed, create it under `D:\DraftAI_agent`.

## Local Commands

Start backend:

```powershell
cd D:\DraftAI_agent\research_paper_agent
python api.py
```

Start frontend:

```powershell
cd D:\DraftAI_agent\docs
python -m http.server 8000
```

Check backend:

```powershell
Invoke-WebRequest -Uri http://127.0.0.1:9000/api/status -UseBasicParsing
```

## Secret Safety

- `D:\DraftAI_agent\research_paper_agent\.env` contains local API credentials and must not be uploaded.
- Keep `.env.example` and `.env.template` as placeholder-only files.
