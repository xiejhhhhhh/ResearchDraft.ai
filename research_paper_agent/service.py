import json
from datetime import datetime
from pathlib import Path
from typing import Any

from config import DATA_DIR
from models import ResearchIdeaRequest

SUBMISSIONS_FILE = DATA_DIR / 'submissions.json'


def _load_submissions() -> list[dict[str, Any]]:
    if not SUBMISSIONS_FILE.exists():
        return []

    try:
        with SUBMISSIONS_FILE.open('r', encoding='utf-8') as handle:
            return json.load(handle)
    except Exception:
        return []


def _save_submissions(submissions: list[dict[str, Any]]) -> None:
    with SUBMISSIONS_FILE.open('w', encoding='utf-8') as handle:
        json.dump(submissions, handle, ensure_ascii=False, indent=2)


def process_research_request(data: dict[str, Any]) -> dict[str, str]:
    request = ResearchIdeaRequest(
        idea=data.get('idea', '').strip(),
        field=data.get('field', '').strip(),
        journal=data.get('journal', None),
        output_format=data.get('output_format', 'tex'),
        email=data.get('email', '').strip(),
    )

    if not request.idea or not request.field or not request.email:
        return {
            'status': 'error',
            'message': '请提供研究主题、研究领域和联系邮箱。',
        }

    submission = {
        'idea': request.idea,
        'field': request.field,
        'journal': request.journal,
        'output_format': request.output_format,
        'email': request.email,
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'status': 'received',
    }

    submissions = _load_submissions()
    submissions.append(submission)
    _save_submissions(submissions)

    return {
        'status': 'success',
        'message': '研究Idea已成功接收，后端服务会继续处理并通过邮箱与您联系。',
    }
