from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional


def _find_latex_executable(names: list[str]) -> Optional[str]:
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    candidate_dirs = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "MiKTeX" / "miktex" / "bin" / "x64",
        Path("C:/Program Files/MiKTeX/miktex/bin/x64"),
    ]
    for directory in candidate_dirs:
        for name in names:
            candidate = directory / name
            if candidate.exists():
                return str(candidate)
    return None


def compile_latex_to_pdf(tex_file: Path) -> tuple[Optional[str], str]:
    """Compile a .tex file into PDF when a local LaTeX engine is available."""
    engine = _find_latex_executable(["xelatex.exe", "xelatex", "pdflatex.exe", "pdflatex"])
    if not engine:
        return None, "Skipped PDF generation: no local LaTeX engine was found. Install MiKTeX or TeX Live and retry."

    bibtex = _find_latex_executable(["bibtex.exe", "bibtex"])
    base_name = tex_file.stem
    log_file = tex_file.with_suffix(".compile.log")
    commands = [
        [engine, "-interaction=nonstopmode", "-halt-on-error", tex_file.name],
    ]
    if bibtex and tex_file.with_suffix(".bib").exists():
        commands.append([bibtex, base_name])
    commands.extend([
        [engine, "-interaction=nonstopmode", "-halt-on-error", tex_file.name],
        [engine, "-interaction=nonstopmode", "-halt-on-error", tex_file.name],
    ])

    log_chunks: list[str] = []
    for command in commands:
        try:
            completed = subprocess.run(
                command,
                cwd=tex_file.parent,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=120,
                check=False,
            )
        except Exception as exc:
            message = f"PDF generation failed while running {' '.join(command)}: {exc}"
            log_chunks.append(message)
            log_file.write_text("\n\n".join(log_chunks), encoding="utf-8")
            return None, message

        log_chunks.append(
            f"$ {' '.join(command)}\n"
            f"exit={completed.returncode}\n"
            f"STDOUT:\n{completed.stdout}\n"
            f"STDERR:\n{completed.stderr}"
        )
        if completed.returncode != 0:
            message = f"PDF generation failed while running {' '.join(command)}. See {log_file.name}."
            log_file.write_text("\n\n".join(log_chunks), encoding="utf-8")
            return None, message

    log_file.write_text("\n\n".join(log_chunks), encoding="utf-8")
    pdf_file = tex_file.with_suffix(".pdf")
    if pdf_file.exists():
        return pdf_file.name, f"PDF generated successfully using {Path(engine).name}."
    return None, f"PDF generation finished but {pdf_file.name} was not created. See {log_file.name}."

