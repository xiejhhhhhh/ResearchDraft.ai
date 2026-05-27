# Changelog

All notable changes to ResearchDraft.ai will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.1.0] - 2026-05-27

### Added
- Zotero collection-based literature import
- External scholarly search (Semantic Scholar, arXiv, Crossref)
- Automatic literature supplementation when collection has fewer than 20 items
- English research draft generation (Markdown, LaTeX, BibTeX, PDF)
- Per-paper HTML literature summaries
- Quality gate checker (section alignment, citation consistency, URL handling, math hygiene, PDF compilation)
- Bilingual frontend (Chinese/English) with language switcher
- Dockerfile for containerized deployment
- Render deployment support (Procfile)
- One-click local setup script (scripts/setup_local.ps1)
- Configuration checker (check_config.py)
- PDF full-text reading support (local Zotero PDFs and open-access downloads via Unpaywall)
- EasyScholar journal ranking integration
- Unit tests for export helpers, literature search, and prompt construction
- Code structure documentation (docs/code_structure.html)

### Changed
- Modularized codebase: literature/, generation/, export/, validation/ packages
- Improved LaTeX compilation with proper package dependencies
- Enhanced BibTeX key generation and citation mapping

### Security
- Path traversal protection for file download endpoints
- .gitignore excludes .env, generated files, and caches
- .env.example with placeholder-only values

## [0.0.1] - 2026-05-06

### Added
- Initial project upload
- Basic Flask backend
- Static frontend
