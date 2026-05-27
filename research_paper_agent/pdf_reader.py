"""PDF/full-text reading helpers for ResearchDraft.ai.

The Zotero Web API always exposes item metadata, but full-text reading depends
on whether a PDF attachment is available and whether the API key can access the
file. These helpers are deliberately conservative: when full text cannot be
loaded, they return structured diagnostics instead of pretending that the paper
was read.
"""

from __future__ import annotations

import re
import os
import hashlib
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

import requests


PDF_REQUEST_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0 Safari/537.36 ResearchDraftAI/0.1'
    ),
    'Accept': 'application/pdf,text/html;q=0.9,*/*;q=0.8',
}


SECTION_ALIASES = {
    'abstract': ['abstract'],
    'introduction': ['introduction', 'background'],
    'methods': [
        'materials and methods',
        'methodology',
        'methods',
        'data and methods',
        'experimental setup',
    ],
    'results': ['results', 'experimental results', 'results and analysis'],
    'discussion': ['discussion', 'results and discussion'],
    'limitations': ['limitations', 'limitation', 'study limitations'],
    'conclusion': ['conclusion', 'conclusions', 'future work'],
    'references': ['references', 'bibliography'],
}


def read_pdf_text(pdf_path: Path) -> str:
    """Extract text from a PDF using pypdf/PyPDF2 when available."""
    if not pdf_path.exists():
        return ''

    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except Exception:
            return ''

    try:
        reader = PdfReader(str(pdf_path))
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or '')
        return '\n'.join(pages).strip()
    except Exception:
        return ''


def _attachment_download_url(attachment: dict[str, Any]) -> Optional[str]:
    links = attachment.get('links') or {}
    enclosure = links.get('enclosure') or {}
    href = enclosure.get('href')
    if href:
        return href
    data = attachment.get('data') or {}
    return data.get('url')


def _max_pdf_bytes() -> int:
    try:
        return int(float(os.getenv('OA_PDF_MAX_MB', '25')) * 1024 * 1024)
    except Exception:
        return 25 * 1024 * 1024


def _safe_pdf_name(seed: str) -> str:
    digest = hashlib.sha1((seed or 'open_access_pdf').encode('utf-8')).hexdigest()[:16]
    return f'oa_{digest}.pdf'


def _looks_like_pdf_url(url: str) -> bool:
    parsed = urlparse(url or '')
    path = parsed.path.lower()
    return path.endswith('.pdf') or '/pdf' in path or 'download' in path


def _candidate_open_access_urls(item: dict[str, Any]) -> list[str]:
    candidates = []
    for key in ('pdf_url', 'open_access_pdf_url'):
        if item.get(key):
            candidates.append(item[key])

    url = item.get('url') or ''
    if url:
        if _looks_like_pdf_url(url):
            candidates.append(url)
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        path = parsed.path.rstrip('/')
        if 'mdpi.com' in host and not path.lower().endswith('/pdf'):
            candidates.append(f'{parsed.scheme}://{parsed.netloc}{path}/pdf')

    doi = (item.get('doi') or '').strip()
    unpaywall_email = os.getenv('UNPAYWALL_EMAIL') or os.getenv('OA_UNPAYWALL_EMAIL')
    if doi and unpaywall_email:
        try:
            response = requests.get(
                f'https://api.unpaywall.org/v2/{doi}',
                params={'email': unpaywall_email},
                timeout=20,
            )
            if response.ok:
                data = response.json()
                best = data.get('best_oa_location') or {}
                for value in (best.get('url_for_pdf'), best.get('url')):
                    if value:
                        candidates.append(value)
        except Exception:
            pass

    deduped = []
    seen = set()
    for url in candidates:
        if url and url not in seen:
            deduped.append(url)
            seen.add(url)
    return deduped


def download_open_access_pdf(item: dict[str, Any], output_dir: Path) -> tuple[Optional[Path], str]:
    """Download an open-access PDF candidate for an external literature item.

    The function only uses explicit OA PDF hints, Unpaywall OA locations, or
    conservative publisher URL transforms. It does not attempt to bypass access
    controls. Downloads are size-limited by ``OA_PDF_MAX_MB``.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    candidates = _candidate_open_access_urls(item)
    if not candidates:
        return None, 'No open-access PDF URL was available for this item.'

    max_bytes = _max_pdf_bytes()
    errors = []
    for url in candidates:
        target = output_dir / _safe_pdf_name(url)
        if target.exists() and target.stat().st_size > 0:
            return target, f'Loaded cached open-access PDF: {url}'

        try:
            with requests.get(
                url,
                headers=PDF_REQUEST_HEADERS,
                stream=True,
                allow_redirects=True,
                timeout=45,
            ) as response:
                response.raise_for_status()
                content_type = response.headers.get('content-type', '')
                content_length = int(response.headers.get('content-length') or 0)
                if content_length and content_length > max_bytes:
                    errors.append(f'{url} skipped because PDF size exceeds OA_PDF_MAX_MB.')
                    continue

                first_chunk = True
                total = 0
                with target.open('wb') as handle:
                    for chunk in response.iter_content(chunk_size=1024 * 256):
                        if not chunk:
                            continue
                        if first_chunk:
                            first_chunk = False
                            if 'pdf' not in content_type.lower() and not chunk.startswith(b'%PDF'):
                                handle.close()
                                target.unlink(missing_ok=True)
                                errors.append(f'{url} did not return PDF content.')
                                break
                        total += len(chunk)
                        if total > max_bytes:
                            handle.close()
                            target.unlink(missing_ok=True)
                            errors.append(f'{url} exceeded OA_PDF_MAX_MB during download.')
                            break
                        handle.write(chunk)
                    else:
                        if target.exists() and target.stat().st_size > 0:
                            return target, f'Downloaded open-access PDF: {url}'
        except Exception as exc:
            target.unlink(missing_ok=True)
            errors.append(f'{url}: {exc}')

    return None, 'Open-access PDF download failed. ' + ' | '.join(errors[:3])


def _default_zotero_storage_dirs() -> list[Path]:
    candidates = []
    configured = os.getenv('ZOTERO_LOCAL_STORAGE_DIR') or os.getenv('ZOTERO_STORAGE_DIR')
    if configured:
        candidates.append(Path(configured))

    user_profile = os.getenv('USERPROFILE')
    if user_profile:
        candidates.append(Path(user_profile) / 'Zotero' / 'storage')

    appdata = os.getenv('APPDATA')
    if appdata:
        candidates.append(Path(appdata) / 'Zotero' / 'Zotero' / 'storage')

    unique = []
    seen = set()
    for path in candidates:
        resolved = str(path)
        if resolved not in seen and path.exists():
            unique.append(path)
            seen.add(resolved)
    return unique


def _normalize_for_match(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r'[a-zA-Z0-9]{3,}', (value or '').lower())
        if token not in {'pdf', 'and', 'the', 'using', 'with', 'from', 'for'}
    }


def find_local_zotero_pdf(
    *,
    attachment_key: str = '',
    attachment_title: str = '',
    attachment_filename: str = '',
    parent_title: str = '',
) -> tuple[Optional[Path], str]:
    """Find a Zotero PDF in the local Zotero storage directory."""
    storage_dirs = _default_zotero_storage_dirs()
    if not storage_dirs:
        return None, 'No local Zotero storage directory was found.'

    for storage_dir in storage_dirs:
        if attachment_key:
            keyed_dir = storage_dir / attachment_key
            if keyed_dir.exists():
                pdfs = list(keyed_dir.glob('*.pdf'))
                if pdfs:
                    return pdfs[0], f'Loaded local Zotero PDF from storage folder {attachment_key}.'

    expected_tokens = (
        _normalize_for_match(attachment_filename)
        | _normalize_for_match(attachment_title)
        | _normalize_for_match(parent_title)
    )
    if not expected_tokens:
        return None, 'No title or filename tokens were available for local PDF matching.'

    best_path = None
    best_score = 0
    for storage_dir in storage_dirs:
        for pdf_path in storage_dir.glob('*/*.pdf'):
            pdf_tokens = _normalize_for_match(pdf_path.name)
            score = len(expected_tokens & pdf_tokens)
            if score > best_score:
                best_path = pdf_path
                best_score = score

    if best_path and best_score >= max(2, min(5, len(expected_tokens) // 3)):
        return best_path, f'Loaded local Zotero PDF by filename/title match with score {best_score}.'

    return None, 'No matching local Zotero PDF was found in storage.'


def download_zotero_pdf(client: Any, item_key: str, output_dir: Path) -> tuple[Optional[Path], str]:
    """Try to download the first PDF attachment for a Zotero item.

    Returns ``(path, status)``. ``path`` is None when no readable PDF is found.
    The function never prints credentials or stores them in files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    parent_title = ''
    try:
        parent = client.item(item_key)
        parent_title = (parent.get('data') or {}).get('title', '')
    except Exception:
        parent_title = ''

    try:
        children = client.children(item_key)
    except Exception as exc:
        local_path, local_status = find_local_zotero_pdf(parent_title=parent_title)
        if local_path:
            return local_path, f'{local_status} Zotero API children lookup failed: {exc}'
        return None, f'Could not list Zotero attachments: {exc}'

    pdf_attachments = []
    for child in children or []:
        data = child.get('data') or {}
        if data.get('itemType') == 'attachment' and (
            data.get('contentType') == 'application/pdf'
            or str(data.get('filename', '')).lower().endswith('.pdf')
            or str(data.get('title', '')).lower().endswith('.pdf')
        ):
            pdf_attachments.append(child)

    if not pdf_attachments:
        local_path, local_status = find_local_zotero_pdf(parent_title=parent_title)
        if local_path:
            return local_path, f'{local_status} Zotero metadata did not expose a PDF attachment.'
        return None, 'No PDF attachment is available through Zotero metadata.'

    attachment = pdf_attachments[0]
    attachment_data = attachment.get('data') or {}
    attachment_key = attachment.get('key') or attachment_data.get('key') or item_key
    attachment_title = attachment_data.get('title', '')
    attachment_filename = attachment_data.get('filename', '')
    local_path, local_status = find_local_zotero_pdf(
        attachment_key=attachment_key,
        attachment_title=attachment_title,
        attachment_filename=attachment_filename,
        parent_title=parent_title,
    )
    if local_path:
        return local_path, local_status

    pdf_path = output_dir / f'{attachment_key}.pdf'
    if pdf_path.exists() and pdf_path.stat().st_size > 0:
        return pdf_path, 'Loaded cached Zotero PDF attachment.'

    url = _attachment_download_url(attachment)
    if not url:
        return None, 'PDF attachment exists, but Zotero did not expose a download URL.'

    headers = {}
    api_key = getattr(client, 'api_key', None)
    if api_key:
        headers['Zotero-API-Key'] = api_key

    try:
        response = requests.get(url, headers=headers, timeout=45)
        response.raise_for_status()
        content_type = response.headers.get('content-type', '')
        if 'pdf' not in content_type.lower() and not response.content.startswith(b'%PDF'):
            return None, 'Attachment download did not return a PDF file.'
        pdf_path.write_bytes(response.content)
        return pdf_path, 'Downloaded Zotero PDF attachment.'
    except Exception as exc:
        return None, f'Could not download Zotero PDF attachment: {exc}'


def extract_sections(text: str) -> dict[str, str]:
    """Extract broad article sections from full text with simple heading rules."""
    if not text:
        return {}

    normalized = re.sub(r'\r\n?', '\n', text)
    normalized = re.sub(r'[ \t]+', ' ', normalized)
    heading_patterns = []
    for section_name, aliases in SECTION_ALIASES.items():
        for alias in aliases:
            heading_patterns.append((section_name, re.compile(rf'(?im)^\s*(\d+\.?\s*)?{re.escape(alias)}\s*$')))

    matches = []
    for section_name, pattern in heading_patterns:
        for match in pattern.finditer(normalized):
            matches.append((match.start(), match.end(), section_name))
    matches.sort(key=lambda row: row[0])

    if not matches:
        return {'full_text': normalized[:60000]}

    sections: dict[str, str] = {}
    for idx, (start, end, section_name) in enumerate(matches):
        next_start = matches[idx + 1][0] if idx + 1 < len(matches) else len(normalized)
        content = normalized[end:next_start].strip()
        if content and section_name not in sections:
            sections[section_name] = content[:30000]
    return sections


def extract_figure_table_captions(text: str, limit: int = 12) -> list[str]:
    """Extract candidate figure/table captions from PDF text."""
    if not text:
        return []

    captions = []
    pattern = re.compile(
        r'(?is)\b((Figure|Fig\.?|Table)\s+\d+[A-Za-z]?\s*[:.\-]\s*.{20,700}?)(?=\n\s*(Figure|Fig\.?|Table)\s+\d+|\n\s*\d+\.?\s+[A-Z][A-Za-z ]{3,40}\n|$)'
    )
    for match in pattern.finditer(text):
        caption = re.sub(r'\s+', ' ', match.group(1)).strip()
        if caption not in captions:
            captions.append(caption)
        if len(captions) >= limit:
            break
    return captions
