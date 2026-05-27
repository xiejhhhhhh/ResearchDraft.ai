from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class QualityIssue:
    severity: str
    code: str
    message: str
    file: str | None = None


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _markdown_headings(content: str) -> list[str]:
    headings: list[str] = []
    for line in content.splitlines():
        match = re.match(r"^#{1,3}\s+(.+?)\s*$", line)
        if match:
            headings.append(match.group(1).strip())
    return headings


def _latex_sections(content: str) -> list[str]:
    sections: list[str] = []
    if "\\begin{abstract}" in content:
        sections.append("Abstract")
    for match in re.finditer(r"\\section\{(.+?)\}", content):
        sections.append(match.group(1).strip())
    return sections


def _normalize_heading(heading: str) -> str:
    heading = re.sub(r"[^a-z0-9]+", " ", heading.lower()).strip()
    aliases = {
        "expected results": "results",
        "methodology": "methods",
        "method": "methods",
        "figure table plan": "figure and table plan",
        "figures and tables": "figure and table plan",
        "reference": "references",
    }
    return aliases.get(heading, heading)


def _bibtex_keys(content: str) -> set[str]:
    return set(re.findall(r"@\w+\s*\{\s*([^,\s]+)", content))


def _latex_citation_keys(content: str) -> set[str]:
    keys: set[str] = set()
    for match in re.finditer(r"\\(?:citep|citet|cite|citealp|citeauthor|citeyear)\*?\{([^}]+)\}", content):
        for key in match.group(1).split(","):
            key = key.strip()
            if key:
                keys.add(key)
    return keys


def _check_file_presence(
    draft_dir: Path,
    file_paths: dict[str, str],
    issues: list[QualityIssue],
) -> dict[str, Path]:
    resolved: dict[str, Path] = {}
    for label, filename in file_paths.items():
        if label == "pdf_status" or not isinstance(filename, str):
            continue
        path = (draft_dir / filename).resolve()
        try:
            path.relative_to(draft_dir.resolve())
        except ValueError:
            issues.append(QualityIssue("error", "artifact_path_escape", f"{label} points outside draft directory.", filename))
            continue
        if not path.exists():
            issues.append(QualityIssue("error", "artifact_missing", f"{label} file was not created.", filename))
            continue
        if path.stat().st_size == 0:
            issues.append(QualityIssue("error", "artifact_empty", f"{label} file is empty.", filename))
        resolved[label] = path
    return resolved


def _check_section_alignment(
    files: dict[str, Path],
    issues: list[QualityIssue],
) -> dict[str, Any]:
    markdown = _read_text(files["markdown"]) if "markdown" in files else ""
    latex = _read_text(files["latex"]) if "latex" in files else ""
    md_headings = _markdown_headings(markdown)
    tex_sections = _latex_sections(latex)
    md_sections = [_normalize_heading(item) for item in md_headings[1:]]
    tex_norm = [_normalize_heading(item) for item in tex_sections]

    if markdown and latex:
        missing_in_tex = [item for item in md_sections if item not in tex_norm and item != "references"]
        missing_in_md = [item for item in tex_norm if item not in md_sections and item != "references"]
        if missing_in_tex:
            issues.append(QualityIssue(
                "warning",
                "section_missing_in_tex",
                f"Markdown sections are missing from LaTeX: {', '.join(missing_in_tex)}.",
                files["latex"].name,
            ))
        if missing_in_md:
            issues.append(QualityIssue(
                "warning",
                "section_missing_in_markdown",
                f"LaTeX sections are missing from Markdown: {', '.join(missing_in_md)}.",
                files["markdown"].name,
            ))

        shared = [item for item in md_sections if item in tex_norm and item != "references"]
        tex_shared = [item for item in tex_norm if item in shared]
        if shared != tex_shared:
            issues.append(QualityIssue(
                "warning",
                "section_order_mismatch",
                "Markdown and LaTeX section order differs.",
                files["latex"].name,
            ))

    return {
        "markdown_headings": md_headings,
        "latex_sections": tex_sections,
    }


def _check_bibliography(
    files: dict[str, Path],
    source_count: int,
    issues: list[QualityIssue],
) -> dict[str, Any]:
    bib_content = _read_text(files["bibtex"]) if "bibtex" in files else ""
    tex_content = _read_text(files["latex"]) if "latex" in files else ""
    bib_keys = _bibtex_keys(bib_content)
    citation_keys = _latex_citation_keys(tex_content)

    if source_count and not bib_content:
        issues.append(QualityIssue("error", "bib_missing", "Source literature exists but no BibTeX file was generated."))
    if bib_content and not bib_keys:
        issues.append(QualityIssue("error", "bib_no_entries", "BibTeX file exists but contains no entries.", files["bibtex"].name))
    if source_count and len(bib_keys) < min(source_count, 20):
        issues.append(QualityIssue(
            "warning",
            "bib_entry_count_low",
            f"BibTeX contains {len(bib_keys)} entries for {source_count} source items.",
            files.get("bibtex").name if "bibtex" in files else None,
        ))
    missing = sorted(citation_keys - bib_keys)
    if missing:
        issues.append(QualityIssue(
            "error",
            "citation_key_missing",
            f"LaTeX cites keys that are absent from BibTeX: {', '.join(missing[:12])}.",
            files.get("latex").name if "latex" in files else None,
        ))
    if "latex" in files and source_count and "\\bibliography{" not in tex_content:
        issues.append(QualityIssue("error", "bibliography_command_missing", "LaTeX output has no bibliography command.", files["latex"].name))
    if "latex" in files and source_count and "\\usepackage" in tex_content and "natbib" not in tex_content:
        issues.append(QualityIssue("warning", "natbib_missing", "LaTeX output does not load natbib.", files["latex"].name))
    if "latex" in files and "hyperref" not in tex_content:
        issues.append(QualityIssue("warning", "hyperref_missing", "LaTeX output does not load hyperref.", files["latex"].name))

    return {
        "bibtex_entry_count": len(bib_keys),
        "latex_citation_count": len(citation_keys),
        "missing_citation_keys": missing,
    }


def _check_latex_hygiene(files: dict[str, Path], issues: list[QualityIssue]) -> dict[str, Any]:
    if "latex" not in files:
        return {}
    tex_content = _read_text(files["latex"])
    begin_equations = len(re.findall(r"\\begin\{equation\}", tex_content))
    end_equations = len(re.findall(r"\\end\{equation\}", tex_content))
    if begin_equations != end_equations:
        issues.append(QualityIssue(
            "error",
            "equation_environment_mismatch",
            f"Equation environment mismatch: {begin_equations} begin vs {end_equations} end.",
            files["latex"].name,
        ))
    if re.search(r"\\\$\s*(?:\r?\n)+\s*\\begin\{equation\}", tex_content):
        issues.append(QualityIssue(
            "warning",
            "stray_escaped_dollar_before_equation",
            "Found an escaped dollar marker immediately before a display equation.",
            files["latex"].name,
        ))
    inline_dollars = re.sub(r"\\\$", "", tex_content).count("$")
    if inline_dollars % 2 != 0:
        issues.append(QualityIssue("error", "unbalanced_inline_math", "LaTeX output has an odd number of inline math delimiters.", files["latex"].name))

    url_count = tex_content.count("http://") + tex_content.count("https://")
    if url_count and ("\\href{" not in tex_content or "\\nolinkurl{" not in tex_content):
        issues.append(QualityIssue(
            "warning",
            "url_not_wrapped",
            "URLs exist but are not consistently wrapped with href/nolinkurl.",
            files["latex"].name,
        ))
    if url_count and "\\usepackage{xurl}" not in tex_content:
        issues.append(QualityIssue("warning", "xurl_missing", "LaTeX output has URLs but does not load xurl.", files["latex"].name))

    return {
        "equation_begin_count": begin_equations,
        "equation_end_count": end_equations,
        "url_count": url_count,
    }


def _check_pdf(file_paths: dict[str, str], files: dict[str, Path], issues: list[QualityIssue]) -> dict[str, Any]:
    pdf_status = file_paths.get("pdf_status", "")
    if "latex" in files and "pdf" not in files:
        issues.append(QualityIssue("error", "pdf_missing", f"PDF was not generated. Status: {pdf_status}"))
    elif "pdf" in files and files["pdf"].suffix.lower() != ".pdf":
        issues.append(QualityIssue("error", "pdf_extension_invalid", "PDF artifact does not end with .pdf.", files["pdf"].name))
    elif "pdf" in files and files["pdf"].stat().st_size < 1024:
        issues.append(QualityIssue("warning", "pdf_too_small", "PDF artifact is unusually small.", files["pdf"].name))
    return {"pdf_status": pdf_status, "pdf_generated": "pdf" in files}


def run_quality_gate(
    *,
    draft_dir: Path,
    file_paths: dict[str, str],
    source_items: list[dict[str, Any]] | None = None,
    submission_id: str | None = None,
) -> dict[str, Any]:
    """Validate generated markdown, LaTeX, BibTeX, and PDF artifacts."""
    issues: list[QualityIssue] = []
    files = _check_file_presence(draft_dir, file_paths, issues)
    section_report = _check_section_alignment(files, issues)
    bibliography_report = _check_bibliography(files, len(source_items or []), issues)
    latex_report = _check_latex_hygiene(files, issues)
    pdf_report = _check_pdf(file_paths, files, issues)

    error_count = sum(1 for item in issues if item.severity == "error")
    warning_count = sum(1 for item in issues if item.severity == "warning")
    return {
        "submission_id": submission_id,
        "status": "passed" if error_count == 0 else "failed",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "error_count": error_count,
        "warning_count": warning_count,
        "issues": [asdict(item) for item in issues],
        "artifacts": {label: path.name for label, path in files.items()},
        "sections": section_report,
        "bibliography": bibliography_report,
        "latex": latex_report,
        "pdf": pdf_report,
    }


def write_quality_report(report: dict[str, Any], output_file: Path) -> str:
    output_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_file.name
