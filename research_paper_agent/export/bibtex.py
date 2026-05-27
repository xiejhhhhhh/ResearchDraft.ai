from __future__ import annotations

import re
from html import unescape
from typing import Any


def extract_year(raw_date: str) -> str:
    match = re.search(r"(19|20)\d{2}", raw_date or "")
    return match.group(0) if match else "n.d."


def citation_key(item: dict[str, Any], index: int) -> str:
    authors = item.get("authors") or []
    first_author = authors[0].split()[-1] if authors else "source"
    year = extract_year(item.get("year", ""))
    title_word_match = re.search(r"[A-Za-z0-9]+", item.get("title", "paper"))
    title_word = title_word_match.group(0) if title_word_match else "paper"
    raw_key = f"{first_author}{year}{title_word}{index + 1}"
    return re.sub(r"[^A-Za-z0-9_:-]", "", raw_key)


def _escape_bibtex_value(value: str) -> str:
    clean = unescape(str(value or "")).replace("\xa0", " ")
    clean = re.sub(r"\s+", " ", clean).strip()
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
    return "".join(replacements.get(char, char) for char in clean)


def generate_bibtex(items: list[dict[str, Any]]) -> str:
    entries = []
    for index, item in enumerate(items or []):
        title = item.get("title") or f"Untitled Zotero Source {index + 1}"
        authors = item.get("authors") or []
        author_text = " and ".join(authors) if authors else "Unknown Author"
        year = extract_year(item.get("year", ""))
        entry_type = "article" if item.get("publication") else "misc"
        fields = {
            "title": title,
            "author": author_text,
            "year": year,
            "journal": item.get("publication", ""),
            "volume": item.get("volume", ""),
            "number": item.get("issue", ""),
            "pages": item.get("pages", ""),
            "doi": item.get("doi", ""),
            "url": item.get("url", ""),
            "publisher": item.get("publisher", ""),
        }
        populated_fields = [
            f"  {name} = {{{_escape_bibtex_value(value)}}}"
            for name, value in fields.items()
            if value
        ]
        entries.append(
            f"@{entry_type}{{{citation_key(item, index)},\n"
            + ",\n".join(populated_fields)
            + "\n}"
        )
    return "\n\n".join(entries) + ("\n" if entries else "")

