from dataclasses import dataclass
from typing import Optional

@dataclass
class ResearchIdeaRequest:
    idea: str
    field: str
    journal: Optional[str]
    output_format: str
    email: str
