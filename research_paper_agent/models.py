from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class ResearchIdeaRequest:
    idea: str
    field: str
    journal: Optional[str]
    output_format: str
    add_to_zotero: bool
    email: str
    collection: Optional[str] = None
    data_description: Optional[str] = None
    literature_mode: str = "zotero"

@dataclass
class ResearchDraft:
    title: str
    abstract: str
    introduction: str
    literature_review: str
    methodology: str
    expected_results: str
    conclusion: str
    references: list[str]
    generated_at: str
    word_count: int
    source_items: list[dict[str, Any]] | None = None
    literature_summary_files: list[str] | None = None
    raw_content: str | None = None
