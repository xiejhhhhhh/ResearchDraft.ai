from __future__ import annotations

import re


def safe_latex(text: str) -> str:
    """Escape the most common LaTeX special characters in generated text."""
    if not text:
        return ""

    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def normalize_url_text(url: str) -> str:
    """Clean URL text that LLMs sometimes space around hyphens."""
    clean = (url or "").strip().rstrip(").,;:")
    clean = re.sub(r"\s*-\s*", "-", clean)
    clean = re.sub(r"\s+", "", clean)
    return clean


def latex_url(url: str) -> str:
    """Render a clickable, line-breakable URL for LaTeX/PDF output."""
    clean = normalize_url_text(url)
    return f"\\href{{{clean}}}{{\\nolinkurl{{{clean}}}}}"


def replace_plain_urls_with_latex(text: str) -> str:
    """Convert plain HTTP URLs to clickable LaTeX links before text escaping."""
    if not text:
        return ""

    url_pattern = re.compile(
        r"https?://[A-Za-z0-9._~:/?#\[\]@!$&'+,;=%-]+"
        r"(?:\s*-\s*[A-Za-z0-9._~:/?#\[\]@!$&'+,;=%-]+)*"
    )
    return url_pattern.sub(lambda match: latex_url(match.group(0)), text)

