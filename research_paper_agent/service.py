import json
import os
import re
from html import escape
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, List, Dict

import openai
from anthropic import Anthropic
from dotenv import load_dotenv
import requests

from config import DATA_DIR
from models import ResearchIdeaRequest, ResearchDraft
from generation.prompts import build_publishable_outline_prompt as _build_publishable_outline_prompt
from literature_analyzer import analyze_literature_items, synthesize_cross_literature
from literature.external_search import build_external_search_query as _build_external_search_query
from literature.external_search import clean_literature_items as _clean_literature_items
from literature.external_search import dedupe_supplemental_items as _dedupe_supplemental_items
from literature.external_search import search_external_literature
from literature.ranking import get_easyscholar_publication_rank
from literature.ranking import parse_easyscholar_rank
from literature.ranking import weight_literature_items
from literature.zotero import add_to_zotero
from literature.zotero import find_collection_key
from literature.zotero import get_or_create_collection
from literature.zotero import get_zotero_client
from literature.zotero import get_zotero_items
from literature.zotero import list_zotero_collections
from literature.zotero import sync_literature_items_to_zotero
from pipeline_generator import generate_pipeline_files
from export.bibtex import citation_key as _citation_key
from export.bibtex import extract_year as _extract_year
from export.bibtex import generate_bibtex as _generate_bibtex
from export.latex_text import replace_plain_urls_with_latex as _replace_plain_urls_with_latex
from export.latex_text import safe_latex as _safe_latex
from export.pdf import compile_latex_to_pdf as _compile_latex_to_pdf
from validation.quality_gate import run_quality_gate, write_quality_report

# Load environment variables
load_dotenv(Path(__file__).resolve().parent / '.env')


def _clear_dead_local_proxy() -> None:
    """Remove placeholder proxy values that break Zotero/API access locally."""
    proxy_vars = [
        'HTTP_PROXY',
        'HTTPS_PROXY',
        'ALL_PROXY',
        'http_proxy',
        'https_proxy',
        'all_proxy',
    ]
    for name in proxy_vars:
        value = os.environ.get(name, '')
        if '127.0.0.1:9' in value or 'localhost:9' in value:
            os.environ.pop(name, None)


_clear_dead_local_proxy()

SUBMISSIONS_FILE = DATA_DIR / 'submissions.json'
DRAFTS_DIR = DATA_DIR / 'drafts'
DRAFTS_DIR.mkdir(exist_ok=True)
LITERATURE_SUMMARIES_DIR = DATA_DIR / 'literature_summaries'
LITERATURE_SUMMARIES_DIR.mkdir(exist_ok=True)


def _split_sentences_for_summary(text: str) -> list[str]:
    """Split metadata text into usable academic sentences."""
    cleaned = re.sub(r'\s+', ' ', text or '').strip()
    sentences = re.split(r'(?<=[.!?])\s+', cleaned)
    return [sentence.strip() for sentence in sentences if len(sentence.strip()) >= 35]


def _pick_summary_sentences(text: str, keywords: list[str], fallback: str, limit: int = 3) -> str:
    """Pick sentences that mention the requested concept, preserving original wording."""
    picked: list[str] = []
    keyword_lowers = [keyword.lower() for keyword in keywords]
    for sentence in _split_sentences_for_summary(text):
        lower = sentence.lower()
        if any(
            (keyword in lower if not re.match(r'^[a-z0-9-]+$', keyword) else re.search(rf'\b{re.escape(keyword)}\b', lower))
            for keyword in keyword_lowers
        ):
            picked.append(sentence)
        if len(picked) >= limit:
            break
    return ' '.join(picked) if picked else fallback


def _infer_data_type_summary(title: str, abstract: str) -> str:
    """Infer a concise data-type description from title and abstract metadata."""
    lower = f"{title} {abstract}".lower()
    parts: list[str] = []
    if any(term in lower for term in ['lsst', 'legacy survey of space and time', 'vera rubin']):
        parts.append('LSST/Rubin time-domain photometric survey data')
    if any(term in lower for term in ['lamost', 'spectra', 'spectroscopic', 'spectrum']):
        parts.append('LAMOST or other spectroscopic observations')
    if any(term in lower for term in ['einstein probe', ' x-ray', 'xray', 'x ray']):
        parts.append('Einstein Probe or other X-ray transient observations')
    if any(term in lower for term in ['fits', 'catalog', 'catalogue', 'light curve', 'lightcurve', 'time-domain', 'time domain']):
        parts.append('FITS catalogs, time-domain light curves, or astronomical image products')
    if any(term in lower for term in ['agn', 'active galactic nuclei', 'quasar', 'blazar']):
        parts.append('AGN, quasar, or blazar monitoring samples')
    if any(term in lower for term in ['sentinel', 'landsat', 'satellite', 'google earth engine', 'synthetic aperture radar']):
        parts.append('satellite remote-sensing data')
    elif 'remote sensing' in lower:
        parts.append('remote-sensing crop observations')
    if any(term in lower for term in ['uav', 'uas', 'drone', 'unmanned aerial', 'aerial imagery']):
        parts.append('UAV or aerial crop imagery')
    if any(term in lower for term in ['hyperspectral']):
        parts.append('hyperspectral crop observations')
    if any(term in lower for term in ['multispectral']):
        parts.append('multispectral crop imagery')
    if any(term in lower for term in ['spectral reflectance', 'spectral signature', 'near infrared', 'shortwave infrared']):
        parts.append('field spectral reflectance measurements')
    if any(term in lower for term in ['leaf image', 'leaf images', 'plant village', 'plantvillage', 'kaggle']):
        parts.append('annotated plant leaf image datasets')
    if any(term in lower for term in ['field sampling', 'field and tuber sampling', 'field survey', 'ground truth', 'laboratory testing']):
        parts.append('field sampling or laboratory ground-truth records')
    if any(term in lower for term in ['meteorological', 'weather', 'climate', 'era5']):
        parts.append('meteorological or climate covariates')
    if any(term in lower for term in ['soil', 'soilgrids']):
        parts.append('soil or edaphic covariates')

    if parts:
        unique_parts = list(dict.fromkeys(parts))
        return 'The study uses ' + ', '.join(unique_parts[:-1]) + (f", and {unique_parts[-1]}" if len(unique_parts) > 1 else unique_parts[0]) + '.'
    if any(term in lower for term in ['astronom', 'telescope', 'survey', 'transient']):
        return 'The study appears to use astronomical survey observations, such as time-domain photometry, spectra, catalogs, or image products.'
    if any(term in lower for term in ['image', 'images', 'vision', 'camera']):
        return 'The study appears to use visual crop observations, such as field images or camera-based plant imagery.'
    if any(term in lower for term in ['remote sensing', 'spectral']):
        return 'The study appears to use remote-sensing or spectral crop-monitoring data.'
    return 'The available metadata does not explicitly identify the dataset.'


def _infer_method_type_summary(title: str, abstract: str) -> str:
    """Infer a concise method-family description from title and abstract metadata."""
    lower = f"{title} {abstract}".lower()
    families: list[str] = []
    def has_any(terms: list[str]) -> bool:
        for term in terms:
            if re.search(rf'\b{re.escape(term)}\b', lower):
                return True
        return False
    if has_any(['support vector', 'svm']):
        families.append('support-vector-machine classification')
    if has_any(['random forest']):
        families.append('random-forest classification')
    if has_any(['xgboost', 'gradient boosting']):
        families.append('tree-based ensemble learning')
    if has_any(['cnn', 'convolutional', 'resnet', 'vggnet', 'googlenet', 'efficientnet']):
        families.append('convolutional deep-learning image classification')
    if has_any(['transformer', 'vision transformer', 'vit', 'attention']):
        families.append('transformer or attention-based modelling')
    if has_any(['bert', 'self-attention', 'cross-attention']):
        families.append('self-attention or cross-attention representation learning')
    if has_any(['lstm', 'gru', 'time series']):
        families.append('temporal sequence modelling')
    if has_any(['forecast', 'prediction', 'predictive', 'outburst', 'transient']):
        families.append('time-domain event prediction')
    if has_any(['multimodal', 'multi-modal']):
        families.append('multimodal data fusion')
    if has_any(['light curve', 'spectra', 'spectral energy distribution', 'sed']):
        families.append('astronomical feature extraction from light curves or spectra')
    if has_any(['vegetation index', 'ndvi', 'spectral index']):
        families.append('vegetation-index or spectral-feature analysis')
    if has_any(['machine learning', 'classifier', 'classification']) and not families:
        families.append('machine-learning classification or predictive modelling')
    if has_any(['deep learning', 'neural network']) and not any('deep-learning' in family for family in families):
        families.append('deep-learning-based modelling')

    if families:
        unique_families = list(dict.fromkeys(families))
        return 'The paper applies ' + ', '.join(unique_families[:-1]) + (f", and {unique_families[-1]}" if len(unique_families) > 1 else unique_families[0]) + '.'
    if any(term in lower for term in ['review', 'survey']):
        return 'The paper is likely a review or synthesis study.'
    if any(term in lower for term in ['astronom', 'agn', 'quasar', 'transient']):
        return 'The method appears to involve astronomical time-domain analysis or machine-learning-based transient/AGN modelling.'
    return 'The method is not fully recoverable from metadata and should be checked in the full paper.'


def _infer_data_method_result_gap(item: dict[str, Any]) -> dict[str, str]:
    """Create a conservative per-paper summary from metadata and abstract text."""
    abstract = item.get('abstract') or ''
    title = item.get('title') or 'Untitled paper'
    data_hint = _infer_data_type_summary(title, abstract)
    method_hint = _infer_method_type_summary(title, abstract)

    result_from_abstract = _pick_summary_sentences(
        abstract,
        [
            'result', 'results', 'accuracy', 'fscore', 'f-score', 'precision',
            'recall', 'performance', 'outperform', 'improve', 'identified',
            'classified', 'detected', 'achieved', 'score', 'scores', 'range',
            'frames per second', '%',
        ],
        abstract[:700] if abstract else 'No abstract is available through the current metadata source.',
        limit=4,
    )

    deep_summary = item.get('deep_summary') or {}
    if deep_summary:
        if deep_summary.get('read_status') != 'metadata_abstract_only':
            data_hint = deep_summary.get('data_used') or data_hint
            method_hint = deep_summary.get('methods') or method_hint
            result_hint = deep_summary.get('scientific_results') or result_from_abstract
        else:
            result_hint = result_from_abstract or deep_summary.get('scientific_results')
        gap_hint = deep_summary.get('limitations') or 'No explicit limitation statement was identified in the available text.'
    else:
        result_hint = result_from_abstract
        gap_hint = 'No full text has been read yet. Limitations are not explicit in metadata and should be checked in Discussion, Conclusion, or Limitations sections.'

    return {
        'data': data_hint,
        'method': method_hint,
        'result': result_hint,
        'gap': gap_hint,
    }


def _extract_reference_keywords(item: dict[str, Any], limit: int = 12, idea: str = '') -> list[str]:
    """Extract lightweight keywords from Zotero/external metadata."""
    existing_tags = [str(tag).strip() for tag in item.get('tags') or [] if str(tag).strip()]
    text = ' '.join([
        item.get('title', ''),
        item.get('abstract', ''),
        item.get('publication', ''),
    ])
    lower_text = text.lower()
    controlled_terms = [
        'potato disease detection',
        'early detection',
        'potato virus y',
        'early blight',
        'late blight',
        'multi-agent machine learning',
        'machine learning',
        'deep learning',
        'remote sensing',
        'uav imagery',
        'hyperspectral imagery',
        'multispectral imagery',
        'sentinel-2',
        'support vector machine',
        'convolutional neural network',
        'efficientnet',
        'transformer',
        'precision agriculture',
        'agn outburst prediction',
        'active galactic nuclei',
        'time-domain astronomy',
        'multimodal transformer',
        'light curve',
        'spectroscopic survey',
        'photometric survey',
        'lsst',
        'lamost',
        'einstein probe',
        'fits catalog',
        'astronomical transient',
    ]
    controlled = [term for term in controlled_terms if term in lower_text]
    if controlled:
        return controlled[:limit]
    stopwords = {
        'using', 'based', 'study', 'paper', 'method', 'methods', 'result', 'results',
        'disease', 'diseases', 'potato', 'detection', 'classification', 'learning',
        'model', 'models', 'data', 'analysis', 'with', 'from', 'this', 'that',
        'were', 'have', 'has', 'for', 'and', 'the', 'into', 'between',
    }
    candidates = []
    for token in re.findall(r'[a-zA-Z][a-zA-Z0-9-]{3,}', lower_text):
        if token not in stopwords and token not in candidates:
            candidates.append(token)
    if idea:
        idea_terms = set(_tokenize_for_relevance(idea))
        filtered = [
            keyword for keyword in controlled + existing_tags + candidates
            if keyword.lower() in idea_terms or any(term in keyword.lower() for term in idea_terms if len(term) >= 5)
        ]
        if filtered:
            return filtered[:limit]
    return (controlled + existing_tags + candidates)[:limit]


def _annotate_citation_positions(items: list[dict[str, Any]], draft: ResearchDraft) -> list[dict[str, Any]]:
    """Mark where each reference appears in the generated outline."""
    section_texts = [
        ('Introduction', draft.introduction or ''),
        ('Literature Synthesis Before Writing', draft.literature_review or ''),
        ('Data/Methods', draft.methodology or ''),
        ('Results', draft.expected_results or ''),
        ('Discussion/Conclusion', draft.conclusion or ''),
        ('Full Outline', draft.raw_content or ''),
    ]

    annotated = []
    for item in items or []:
        authors = item.get('authors') or []
        first_author = authors[0].split()[-1] if authors else ''
        year = _extract_year(item.get('year', ''))
        title_tokens = [
            token for token in _tokenize_for_relevance(item.get('title', ''))
            if len(token) >= 5
        ][:4]
        positions = []

        for section_name, text in section_texts:
            if not text:
                continue
            paragraphs = [para.strip() for para in re.split(r'\n\s*\n|(?<=\.)\s{2,}', text) if para.strip()]
            if not paragraphs:
                paragraphs = [text]
            for idx, paragraph in enumerate(paragraphs, start=1):
                lower = paragraph.lower()
                has_author_year = first_author and first_author.lower() in lower and year != 'n.d.' and year in lower
                has_title_overlap = title_tokens and sum(1 for token in title_tokens if token in lower) >= min(2, len(title_tokens))
                if has_author_year or has_title_overlap:
                    positions.append(f'{section_name}, paragraph {idx}')
                    break

        copied = dict(item)
        copied['cited_position'] = '; '.join(dict.fromkeys(positions)) if positions else 'Not cited in the generated outline.'
        copied['keywords'] = _extract_reference_keywords(item)
        annotated.append(copied)
    return annotated


def _save_literature_summaries(items: list[dict[str, Any]], submission_id: str, idea: str = '') -> list[str]:
    """Save one HTML summary per cited paper under a submission-specific folder."""
    task_dir = LITERATURE_SUMMARIES_DIR / submission_id
    task_dir.mkdir(parents=True, exist_ok=True)
    files = []
    for index, item in enumerate(items or [], start=1):
        hints = _infer_data_method_result_gap(item)
        origin = item.get('reference_origin') or item.get('source') or 'existing_zotero'
        prefix = 'supplemental' if 'supplemental' in origin or 'external' in origin else 'existing'
        filename = f"{prefix}_{index:02d}.html"
        relative_path = f"{submission_id}/{filename}"
        path = task_dir / filename
        authors = ', '.join(item.get('authors') or []) or 'Unknown author'
        keywords = _extract_reference_keywords(item, idea=idea) or item.get('keywords') or _extract_reference_keywords(item)
        keyword_html = ', '.join(escape(keyword) for keyword in keywords) or 'No keywords were extracted.'
        cited_position = item.get('cited_position') or 'Not cited in the generated outline.'
        abstract_summary = item.get('abstract') or 'No abstract metadata is available.'
        html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(item.get('title') or 'Literature Summary')}</title>
  <style>
    body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; line-height: 1.6; color: #1f2937; }}
    h1 {{ font-size: 26px; }}
    h2 {{ margin-top: 28px; font-size: 18px; color: #0f3b82; }}
    .meta {{ color: #64748b; }}
    .weight {{ padding: 8px 12px; background: #eef5ff; border-left: 4px solid #1a6cff; }}
  </style>
</head>
<body>
  <h1>{escape(item.get('title') or 'Untitled paper')}</h1>
  <p class="meta">{escape(authors)}. {escape(_extract_year(item.get('year', '')))}. {escape(item.get('publication') or '')}</p>
  <p class="weight"><strong>Citation weight:</strong> {item.get('citation_weight', 'n/a')} |
  <strong>Relevance:</strong> {item.get('relevance_score', 'n/a')} |
  <strong>Authority proxy:</strong> {item.get('authority_score', 'n/a')} |
  <strong>Journal score:</strong> {item.get('journal_score', 'n/a')}</p>
  <p class="meta"><strong>Journal rank labels:</strong> {escape(', '.join(item.get('journal_rank_labels') or []) or 'No EasyScholar rank found')}</p>
  <h2>Abstract Summary</h2>
  <p>{escape(abstract_summary)}</p>
  <h2>Keywords</h2>
  <p>{keyword_html}</p>
  <h2>Cited Position in This Outline</h2>
  <p>{escape(cited_position)}</p>
  <h2>Data Used</h2>
  <p>{escape(hints['data'])}</p>
  <h2>Methods</h2>
  <p>{escape(hints['method'])}</p>
  <h2>Scientific Results</h2>
  <p>{escape(hints['result'])}</p>
  <h2>Source</h2>
  <p><a href="{escape(item.get('url') or '#')}">{escape(item.get('url') or 'No URL available')}</a></p>
</body>
</html>
"""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
        files.append(relative_path)
    return files


def _normalize_export_heading(heading: str) -> str:
    """Map model headings to stable manuscript sections for Markdown/LaTeX export."""
    cleaned = re.sub(r'^\s*#+\s*', '', heading or '').strip().rstrip(':')
    lower = cleaned.lower()
    if lower == 'title':
        return 'Title'
    if lower == 'abstract':
        return 'Abstract'
    if lower in {'literature synthesis before writing', 'literature review'}:
        return 'Literature Synthesis Before Writing'
    if lower == 'introduction':
        return 'Introduction'
    if lower == 'data':
        return 'Data'
    if lower in {'methods', 'methodology', 'data and methodology'}:
        return 'Methods'
    if lower in {'results', 'expected results'}:
        return 'Results'
    if lower in {'figure and table plan', 'figure plan', 'table plan'}:
        return 'Figure and Table Plan'
    if lower in {'discussion', 'conclusion'}:
        return 'Discussion'
    if lower == 'references':
        return 'References'
    return cleaned


def _extract_sections_from_raw_content(raw_content: str) -> list[tuple[str, str]]:
    """Extract ordered top-level markdown sections from the LLM response."""
    sections: list[tuple[str, list[str]]] = []
    current_title: Optional[str] = None
    current_lines: list[str] = []

    for raw_line in (raw_content or '').splitlines():
        match = re.match(r'^\s*#\s+(.+?)\s*$', raw_line)
        if match:
            if current_title is not None:
                sections.append((current_title, current_lines))
            current_title = _normalize_export_heading(match.group(1))
            current_lines = []
            continue
        if current_title is not None:
            current_lines.append(raw_line)

    if current_title is not None:
        sections.append((current_title, current_lines))

    normalized: list[tuple[str, str]] = []
    for title, lines in sections:
        if title == 'Title':
            continue
        body = '\n'.join(lines).strip()
        if body:
            normalized.append((title, body))
    return normalized


def _draft_sections_for_export(draft: ResearchDraft) -> list[tuple[str, str]]:
    """Return one canonical section list used by both Markdown and LaTeX exporters."""
    if draft.raw_content and len(draft.raw_content.strip()) > 1000:
        raw_sections = _extract_sections_from_raw_content(draft.raw_content)
        if raw_sections:
            preferred_order = [
                'Abstract',
                'Literature Synthesis Before Writing',
                'Introduction',
                'Data',
                'Methods',
                'Results',
                'Figure and Table Plan',
                'Discussion',
                'References',
            ]
            by_title: dict[str, str] = {}
            extras: list[tuple[str, str]] = []
            for title, body in raw_sections:
                if title in preferred_order and title not in by_title:
                    by_title[title] = body
                elif title in preferred_order:
                    by_title[title] = f"{by_title[title]}\n\n{body}"
                else:
                    extras.append((title, body))
            ordered = [(title, by_title[title]) for title in preferred_order if by_title.get(title)]
            return ordered + extras

    return [
        ('Abstract', draft.abstract),
        ('Literature Synthesis Before Writing', draft.literature_review),
        ('Introduction', draft.introduction),
        ('Methods', draft.methodology),
        ('Results', draft.expected_results),
        ('Discussion', draft.conclusion),
        ('References', '\n'.join(f"{i + 1}. {ref}" for i, ref in enumerate(draft.references))),
    ]


def _has_display_math(content: str) -> bool:
    return bool(re.search(r'(\\\[|\\begin\{equation\}|\$\$)', content or ''))


def _ensure_formula_blocks(sections: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Do not inject generic equations into drafts.

    Earlier versions added NDVI and generic classification equations whenever
    the model omitted formulas. That was brittle for non-crop topics such as
    AGN forecasting, so equations are now generated only by the model prompt
    and then normalized during Markdown/LaTeX export.
    """
    return sections


def _normalize_markdown_math(text: str) -> str:
    """Normalize common LLM math delimiters before Markdown/LaTeX export."""
    if not text:
        return ''

    normalized = text.replace('\r\n', '\n')

    # Put existing display math delimiters on their own paragraph. LLMs often
    # emit prose immediately followed by "\[ ... \]" without blank lines; if
    # we do not normalize that first, the lightweight Markdown converter treats
    # the equation as plain text and escapes every LaTeX command.
    normalized = re.sub(
        r'\\\[\s*([\s\S]*?)\s*\\\]',
        lambda m: f"\n\n$$\n{m.group(1).strip()}\n$$\n\n",
        normalized,
    )

    normalized = re.sub(
        r'\$\$\s*([\s\S]*?)\s*\$\$',
        lambda m: f"\n\n$$\n{m.group(1).strip()}\n$$\n\n",
        normalized,
    )

    # Convert standalone single-dollar math blocks, including multiline forms
    # like "$L =\n\\alpha L_{ce}...$", into display math.
    def display_repl(match: re.Match) -> str:
        body = match.group(1).strip()
        return f"\n\n$$\n{body}\n$$\n\n"

    normalized = re.sub(
        r'(?m)(?<!\$)^\s*\$(?!\$)\s*([\s\S]*?)\s*(?<!\$)\$\s*$',
        display_repl,
        normalized,
    )

    # If an inline $... marker is left open before a line break, close it on
    # the same line. This is safer than pairing it with a later dollar sign in
    # another sentence, which can accidentally turn prose into a broken display
    # equation.
    normalized = re.sub(
        r'(?<!\$)\$(?!\$)([^$\n]{1,120})(?=\n)',
        lambda m: f"${m.group(1).strip()}$",
        normalized,
    )

    # If the model leaves an inline \( marker open at a line break, keep the
    # symbol as inline math instead of letting it break the following block.
    normalized = re.sub(
        r'\\\(([A-Za-z0-9_{}^\\,.\-\s]+)\s*(?=\n)',
        lambda m: f"${m.group(1).strip()}$",
        normalized,
    )
    return normalized


def _format_literature_synthesis_section(content: str) -> str:
    """Make one-reference-per-paragraph literature synthesis easier to read."""
    lines = [line.strip() for line in (content or '').splitlines()]
    paragraphs: list[str] = []
    current: list[str] = []
    for line in lines:
        if not line:
            if current:
                paragraphs.append(' '.join(current).strip())
                current = []
            continue
        if re.match(r'^[-*]\s+', line):
            if current:
                paragraphs.append(' '.join(current).strip())
            current = [re.sub(r'^[-*]\s+', '', line).strip()]
        else:
            current.append(line)
    if current:
        paragraphs.append(' '.join(current).strip())
    return '\n\n'.join(paragraphs) if paragraphs else (content or '').strip()


def _strip_markdown_emphasis(text: str) -> str:
    """Remove lightweight Markdown emphasis that should not appear in LaTeX."""
    if not text:
        return ''
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'\1', text)
    return text


def _inject_literature_synthesis_citations(content: str, source_items: list[dict[str, Any]]) -> str:
    """Ensure every literature synthesis paragraph starts with a valid BibTeX citation.

    LLMs often write paragraphs like "**Faisst et al. (2019)**: ..."; the
    generic author-year replacer can miss non-ASCII names or variants without
    commas. Since this section is generated in the same order as source_items,
    we can safely attach the corresponding BibTeX key by paragraph index.
    """
    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(r'\n\s*\n', _format_literature_synthesis_section(content or ''))
        if paragraph.strip()
    ]
    if not paragraphs:
        return content or ''

    rendered: list[str] = []
    for index, paragraph in enumerate(paragraphs):
        clean = _strip_markdown_emphasis(paragraph).strip()
        if re.search(r'\\cite[talp]?\{[^}]+\}', clean):
            rendered.append(clean)
            continue
        if index < len(source_items or []):
            key = _citation_key(source_items[index], index)
            # Remove an author/year lead-in because \citet{key} will render it.
            clean = re.sub(
                r'^[A-Z脌-脰脴-脼][^:]{0,140}\((?:19|20)\d{2}\)\s*:?\s*',
                '',
                clean,
                count=1,
            )
            rendered.append(f"\\citet{{{key}}}: {clean}")
        else:
            rendered.append(clean)
    return '\n\n'.join(rendered)


def _render_markdown_draft(draft: ResearchDraft, sections: list[tuple[str, str]]) -> str:
    """Render Markdown from canonical sections."""
    body = [f"# {draft.title.strip() or 'Untitled Research Draft'}"]
    for title, content in sections:
        if content:
            content = _normalize_markdown_math(content)
            if title == 'Literature Synthesis Before Writing':
                content = _format_literature_synthesis_section(content)
            body.append(f"## {title}\n{content.strip()}")
    body.append(f"---\nGenerated at: {draft.generated_at}\nWord count: {draft.word_count} words")
    return "\n\n".join(body) + "\n"


def _latex_escape_preserving_math(text: str) -> str:
    """Escape text while preserving existing inline/display LaTeX math."""
    if not text:
        return ''
    text = _replace_plain_urls_with_latex(text)
    parts = re.split(r'(\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\)|\$\$[\s\S]*?\$\$|\$(?!\$)[^\n$]+?(?<!\$)\$|\\cite[talp]?\{[^}]+\}|\\href\{[^}]+\}\{\\nolinkurl\{[^}]+\}\})', text)
    output = []
    for part in parts:
        if not part:
            continue
        if (
            (part.startswith('\\[') and part.endswith('\\]')) or
            (part.startswith('\\(') and part.endswith('\\)')) or
            (part.startswith('$$') and part.endswith('$$')) or
            (part.startswith('$') and part.endswith('$') and not part.startswith('$$')) or
            re.fullmatch(r'\\cite[talp]?\{[^}]+\}', part) or
            re.fullmatch(r'\\href\{[^}]+\}\{\\nolinkurl\{[^}]+\}\}', part)
        ):
            output.append(part)
        else:
            output.append(_safe_latex(part))
    return ''.join(output)


def _build_citation_replacements(source_items: list[dict[str, Any]]) -> dict[tuple[str, str], str]:
    """Build author-year to BibTeX key mapping for natbib conversion."""
    replacements: dict[tuple[str, str], str] = {}
    for index, item in enumerate(source_items or []):
        authors = item.get('authors') or []
        if not authors:
            continue
        first_author = authors[0].split()[-1]
        year = _extract_year(item.get('year', ''))
        if not first_author or year == 'n.d.':
            continue
        replacements[(first_author.lower(), year)] = _citation_key(item, index)
    return replacements


def _replace_author_year_citations(text: str, citation_map: dict[tuple[str, str], str]) -> str:
    """Convert common author-year prose citations to natbib commands."""
    if not text or not citation_map:
        return text

    author_pattern = r'([A-Z?-??-?][A-Za-z?-??-??-?\-]+)'

    def parenthetical_repl(match: re.Match) -> str:
        inner = match.group(1)
        keys = []
        inner_lower = inner.lower()
        for (author, year), key in citation_map.items():
            if author in inner_lower and year in inner:
                keys.append(key)
        return f"\\citep{{{','.join(dict.fromkeys(keys))}}}" if keys else match.group(0)

    text = re.sub(r'\(([^()]*?(?:19|20)\d{2}[^()]*)\)', parenthetical_repl, text)

    def textual_repl(match: re.Match) -> str:
        author = match.group(1)
        year = match.group(2)
        key = citation_map.get((author.lower(), year))
        return f"\\citet{{{key}}}" if key else match.group(0)

    text = re.sub(r'\b' + author_pattern + r'\s+et al\.\s*\(((?:19|20)\d{2})\)', textual_repl, text)
    text = re.sub(r'\b' + author_pattern + r'\s*\(((?:19|20)\d{2})\)', textual_repl, text)
    text = re.sub(r'\b' + author_pattern + r'(?:\s+et al\.)?\s+((?:19|20)\d{2})', textual_repl, text)
    return text


def _markdown_body_to_latex(text: str, citation_map: Optional[dict[tuple[str, str], str]] = None) -> str:
    """Convert lightweight markdown body text to cleaner LaTeX text."""
    text = _normalize_markdown_math(_replace_author_year_citations(text or '', citation_map or {}))
    blocks = re.split(r'\n\s*\n', text.strip())
    rendered_blocks = []
    in_itemize = False

    def close_itemize() -> None:
        nonlocal in_itemize
        if in_itemize:
            rendered_blocks.append('\\end{itemize}')
            in_itemize = False

    for block in blocks:
        stripped_block = block.strip()
        if not stripped_block:
            continue
        if re.fullmatch(r'(\\\[[\s\S]*?\\\]|\$\$[\s\S]*?\$\$|\$(?!\$)[\s\S]*?(?<!\$)\$)', stripped_block):
            close_itemize()
            if stripped_block.startswith('$$'):
                math_body = stripped_block.strip('$').strip()
                rendered_blocks.append(f"\\begin{{equation}}\n{math_body}\n\\end{{equation}}")
            elif stripped_block.startswith('$'):
                math_body = stripped_block[1:-1].strip()
                rendered_blocks.append(f"\\begin{{equation}}\n{math_body}\n\\end{{equation}}")
            else:
                math_body = stripped_block[2:-2].strip()
                rendered_blocks.append(f"\\begin{{equation}}\n{math_body}\n\\end{{equation}}")
            continue

        for raw_line in stripped_block.splitlines():
            line = raw_line.rstrip()
            if not line:
                continue
            if re.match(r'^\s*#{2,6}\s+', line):
                close_itemize()
                heading = re.sub(r'^\s*#{2,6}\s+', '', line).strip()
                rendered_blocks.append(f"\\subsection*{{{_safe_latex(heading)}}}")
            elif re.match(r'^\s*[-*]\s+', line):
                if not in_itemize:
                    rendered_blocks.append('\\begin{itemize}')
                    in_itemize = True
                item_text = re.sub(r'^\s*[-*]\s+', '', line).strip()
                rendered_blocks.append(f"\\item {_latex_escape_preserving_math(item_text)}")
            else:
                close_itemize()
                rendered_blocks.append(_latex_escape_preserving_math(line))
    close_itemize()
    return '\n\n'.join(rendered_blocks).strip()


def _render_latex_draft(
    draft: ResearchDraft,
    sections: list[tuple[str, str]],
    base_filename: str,
    source_items: list[dict[str, Any]],
) -> str:
    """Render LaTeX from the same canonical sections used for Markdown."""
    citation_map = _build_citation_replacements(source_items)
    bibliography_line = (
        f"\\nocite{{*}}\n\\bibliographystyle{{plainnat}}\n\\bibliography{{{base_filename}}}"
        if source_items else
        "\\begin{enumerate}\n" + "\n".join(f"\\item {_safe_latex(ref)}" for ref in draft.references) + "\n\\end{enumerate}"
    )
    rendered_sections = []
    abstract_content = ''
    for title, content in sections:
        if title == 'References':
            continue
        if title == 'Abstract':
            abstract_content = _markdown_body_to_latex(content, citation_map)
            continue
        if title == 'Literature Synthesis Before Writing':
            content = _inject_literature_synthesis_citations(content, source_items)
        else:
            content = _strip_markdown_emphasis(content)
        rendered_sections.append(
            f"\\section{{{_safe_latex(title)}}}\n{_markdown_body_to_latex(content, citation_map)}"
        )

    return f"""\\documentclass[12pt]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[T1]{{fontenc}}
\\usepackage{{newtxtext,newtxmath}}
\\usepackage{{amsmath}}
\\usepackage[authoryear,round]{{natbib}}
\\usepackage{{geometry}}
\\usepackage{{microtype}}
\\usepackage{{setspace}}
\\usepackage{{xurl}}
\\usepackage[colorlinks=true,linkcolor=blue,citecolor=blue,urlcolor=blue]{{hyperref}}
\\hypersetup{{breaklinks=true}}
\\geometry{{a4paper, margin=1in}}
\\setstretch{{1.08}}
\\title{{{_safe_latex(draft.title)}}}
\\author{{ResearchDraft.ai}}
\\date{{\\today}}

\\begin{{document}}

\\maketitle

\\begin{{abstract}}
{abstract_content}
\\end{{abstract}}

{chr(10).join(rendered_sections)}

{bibliography_line}

\\end{{document}}
"""


def _save_draft_to_file(
    draft: ResearchDraft,
    output_format: str,
    submission_id: str,
    request: Optional[ResearchIdeaRequest] = None,
) -> Dict[str, str]:
    """Save draft to separate files based on output format."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_filename = f"draft_{submission_id}_{timestamp}"

    file_paths = {}

    sections = _draft_sections_for_export(draft)
    sections = _ensure_formula_blocks(sections)
    full_content = _render_markdown_draft(draft, sections)

    md_file = DRAFTS_DIR / f"{base_filename}.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(full_content)
    file_paths['markdown'] = md_file.name

    source_items = draft.source_items or []
    if source_items:
        bib_file = DRAFTS_DIR / f"{base_filename}.bib"
        with open(bib_file, 'w', encoding='utf-8') as f:
            f.write(_generate_bibtex(source_items))
        file_paths['bibtex'] = bib_file.name

    if output_format == 'tex':
        tex_content = _render_latex_draft(draft, sections, base_filename, source_items)
        tex_file = DRAFTS_DIR / f"{base_filename}.tex"
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.write(tex_content)
        file_paths['latex'] = tex_file.name
        pdf_name, pdf_status = _compile_latex_to_pdf(tex_file)
        if pdf_name:
            file_paths['pdf'] = pdf_name
        file_paths['pdf_status'] = pdf_status

    if output_format == 'docx':
        txt_file = DRAFTS_DIR / f"{base_filename}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(full_content)
        file_paths['text'] = txt_file.name

    demo_data_file = DRAFTS_DIR / f"demo_data_{submission_id}.py"
    if not demo_data_file.exists():
        demo_data_file.write_text(
            '''"""Demo data construction workflow generated by ResearchDraft.ai.

Replace file paths and platform-specific loaders with real project data loaders
before using this script for analysis.
"""

from __future__ import annotations

import numpy as np


def normalize_feature(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    return (x - np.nanmean(x)) / (np.nanstd(x) + 1e-8)


def temporal_aggregate(series: np.ndarray, window: int = 3) -> np.ndarray:
    series = np.asarray(series, dtype=float)
    if series.ndim == 1:
        series = series[:, None]
    output = []
    for idx in range(series.shape[0]):
        start = max(0, idx - window + 1)
        output.append(np.nanmean(series[start:idx + 1], axis=0))
    return np.vstack(output)


def build_demo_features(primary_series, secondary_series=None, static_features=None, image_features=None):
    blocks = [
        normalize_feature(temporal_aggregate(primary_series)),
    ]
    if secondary_series is not None:
        blocks.append(normalize_feature(temporal_aggregate(secondary_series)))
    if static_features is not None:
        blocks.append(normalize_feature(static_features))
    if image_features is not None:
        blocks.append(normalize_feature(image_features))
    return np.concatenate(blocks, axis=-1)
''',
            encoding='utf-8',
        )
    file_paths['demo_data'] = demo_data_file.name

    demo_method_file = DRAFTS_DIR / f"demo_method_{submission_id}.py"
    if not demo_method_file.exists():
        demo_method_file.write_text(
            '''"""Demo multi-agent disease-risk modelling workflow.

This script is a lightweight implementation scaffold. It is intended to make
the manuscript methods auditable before a full model is implemented.
"""

from __future__ import annotations

import numpy as np


def softmax(logits: np.ndarray) -> np.ndarray:
    logits = np.asarray(logits, dtype=float)
    shifted = logits - np.max(logits, axis=-1, keepdims=True)
    exp = np.exp(shifted)
    return exp / (np.sum(exp, axis=-1, keepdims=True) + 1e-8)


def agent_prediction(features: np.ndarray, weights: np.ndarray) -> np.ndarray:
    return softmax(features @ weights)


def fuse_agents(agent_outputs: list[np.ndarray], reliability: np.ndarray) -> np.ndarray:
    reliability = np.asarray(reliability, dtype=float)
    reliability = reliability / (reliability.sum() + 1e-8)
    stacked = np.stack(agent_outputs, axis=0)
    return np.tensordot(reliability, stacked, axes=(0, 0))


def event_risk_score(probabilities: np.ndarray, event_class_index: int = 1) -> np.ndarray:
    return np.asarray(probabilities)[..., event_class_index]
''',
            encoding='utf-8',
        )
    file_paths['demo_method'] = demo_method_file.name

    if request is not None:
        contextual_files = generate_pipeline_files(
            request=request,
            items=draft.source_items or [],
            cross_synthesis=synthesize_cross_literature(draft.source_items or []),
            output_dir=DRAFTS_DIR,
            submission_id=submission_id,
        )
        file_paths.update(contextual_files)

    quality_report = run_quality_gate(
        draft_dir=DRAFTS_DIR,
        file_paths=file_paths,
        source_items=draft.source_items or [],
        submission_id=submission_id,
    )
    quality_file = DRAFTS_DIR / f"quality_report_{base_filename}.json"
    file_paths['quality_report'] = write_quality_report(quality_report, quality_file)

    return file_paths


def _load_quality_report_from_files(file_paths: dict[str, str]) -> dict[str, Any]:
    report_name = file_paths.get('quality_report')
    if not report_name:
        return {}
    report_file = (DRAFTS_DIR / report_name).resolve()
    try:
        report_file.relative_to(DRAFTS_DIR.resolve())
    except ValueError:
        return {}
    if not report_file.exists():
        return {}
    try:
        return json.loads(report_file.read_text(encoding='utf-8'))
    except Exception:
        return {}


def generate_research_draft(request: ResearchIdeaRequest, submission_id: Optional[str] = None) -> Optional[ResearchDraft]:
    """Generate a research draft using Zotero-first or external-only literature retrieval."""
    literature_results = []
    try:
        mode = (request.literature_mode or 'zotero').strip().lower()
        collection_name = (request.collection or '').strip()
        minimum_reference_count = 20

        zotero_client = None
        if mode == 'zotero':
            if not collection_name:
                print("No Zotero collection was provided. Draft generation stopped.")
                return None

            zotero_client = get_zotero_client()
            if not zotero_client:
                print("Zotero client is not available. Draft generation stopped.")
                return None

            literature_results = get_zotero_items(zotero_client, collection=collection_name, limit=50)
            if not literature_results:
                print(f"Collection '{collection_name}' was not found or contains no usable Zotero items. Draft generation stopped.")
                return None

            source_label = f'Zotero collection: {collection_name}'
            print(f"Found {len(literature_results)} Zotero items from collection '{collection_name}'")

            if len(literature_results) < minimum_reference_count:
                needed = minimum_reference_count - len(literature_results)
                supplemental_query = _build_external_search_query(request, literature_results)
                print(f"Collection has {len(literature_results)} items; searching {needed} supplemental references with query: {supplemental_query}")
                supplemental = search_external_literature(supplemental_query, limit=max(needed * 2, needed))
                supplemental = _dedupe_supplemental_items(literature_results, supplemental)[:needed]
                if supplemental:
                    for item in supplemental:
                        item['reference_origin'] = 'supplemental_external'
                    literature_results.extend(supplemental)
                    source_label += (
                        f"; plus {len(supplemental)} supplemental external references "
                        f"because fewer than {minimum_reference_count} Zotero items were available"
                    )
                else:
                    source_label += (
                        f"; external supplementation attempted but returned no usable records "
                        f"for query '{supplemental_query}'"
                    )
        elif mode == 'external':
            supplemental_query = _build_external_search_query(request, literature_results)
            literature_results = search_external_literature(supplemental_query, limit=minimum_reference_count)
            literature_results = _clean_literature_items(literature_results, supplemental_query)[:minimum_reference_count]
            if not literature_results:
                print("External scholarly search returned no usable literature. Draft generation stopped.")
                return None
            for item in literature_results:
                item['reference_origin'] = 'supplemental_external'
            source_label = f'external scholarly search: {supplemental_query}'
            print(f"Found {len(literature_results)} external scholarly items")
        else:
            print(f"Invalid literature mode '{mode}'.")
            return None

        literature_results = weight_literature_items(literature_results, request.idea, request.journal)[:20]
        literature_results = analyze_literature_items(
            literature_results,
            submission_id or 'interactive',
            zotero_client=zotero_client,
            pdf_cache_dir=DATA_DIR / 'pdf_cache' / (submission_id or 'interactive'),
            max_fulltext=0,
        )
        cross_synthesis = synthesize_cross_literature(literature_results)

        literature_context = "\n\nLiterature source used for this draft: " + source_label + "\n"
        literature_context += "Use only the following literature items as the reference source. Do not invent additional references:\n"
        literature_context += "\nCross-paper synthesis extracted before writing:\n"
        literature_context += f"- Shared data patterns: {cross_synthesis.get('data_patterns', '')}\n"
        literature_context += f"- Shared method patterns: {cross_synthesis.get('method_patterns', '')}\n"
        literature_context += f"- Shared limitation patterns: {cross_synthesis.get('limitation_patterns', '')}\n"
        literature_context += f"- Shared result patterns: {cross_synthesis.get('result_patterns', '')}\n"
        literature_context += "\n".join([
            (
                f"- Title: {item.get('title', 'Unknown Title')}\n"
                f"  Reference origin: {item.get('reference_origin', item.get('source', 'existing_zotero'))}\n"
                f"  Authors: {', '.join(item.get('authors', [])) or 'Unknown Author'}\n"
                f"  Year: {_extract_year(item.get('year', ''))}\n"
                f"  Journal: {item.get('publication', '')}\n"
                f"  DOI: {item.get('doi', '')}\n"
                f"  Citation weight: {item.get('citation_weight', 'n/a')}\n"
                f"  Journal score: {item.get('journal_score', 'n/a')}\n"
                f"  Journal ranks: {', '.join(item.get('journal_rank_labels') or [])}\n"
                f"  Abstract: {(item.get('abstract') or '')[:900]}\n"
                f"  Data used: {(item.get('deep_summary') or {}).get('data_used', '')}\n"
                f"  Methods: {(item.get('deep_summary') or {}).get('methods', '')}\n"
                f"  Scientific results: {(item.get('deep_summary') or {}).get('scientific_results', '')}\n"
                f"  Keywords: {', '.join(item.get('keywords') or _extract_reference_keywords(item))}\n"
                f"  Limitations: {(item.get('deep_summary') or {}).get('limitations', '')}"
            )
            for item in literature_results[:20]
        ])

        draft = None

        volcengine_key = os.getenv('VOLCENGINE_API_KEY') or os.getenv('ARK_API_KEY')
        volcengine_model = os.getenv('VOLCENGINE_MODEL_ID') or os.getenv('WORKER_CLONE_MODEL')
        if volcengine_key and volcengine_model:
            draft = _generate_with_volcengine(request, literature_context)

        openai_key = os.getenv('OPENAI_API_KEY') or ''
        if not draft and openai_key and 'your_' not in openai_key.lower():
            draft = _generate_with_openai(request, literature_context)

        anthropic_key = os.getenv('ANTHROPIC_API_KEY') or ''
        if not draft and anthropic_key and 'your_' not in anthropic_key.lower():
            draft = _generate_with_claude(request, literature_context)

        if not draft:
            print("Warning: AI API calls failed or are not configured. Using TEST mock generation with Zotero context.")
            draft = _generate_enhanced_mock_draft(request, literature_results)

        if draft:
            draft.source_items = literature_results
        return draft
    except Exception as e:
        print(f"Error generating draft: {e}")
        if literature_results:
            draft = _generate_enhanced_mock_draft(request, literature_results)
            draft.source_items = literature_results
            return draft
        return None


def _generate_with_openai(request: ResearchIdeaRequest, literature_context: str = "") -> Optional[ResearchDraft]:
    """Generate draft using OpenAI"""
    try:
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        prompt = _build_publishable_outline_prompt(request, literature_context)

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=8000,
            temperature=0.7
        )

        content = response.choices[0].message.content
        return _parse_structured_ai_response(content, fallback_title=request.idea)

    except Exception as e:
        print(f"OpenAI generation failed: {e}")
        return None


def _generate_with_claude(request: ResearchIdeaRequest, literature_context: str = "") -> Optional[ResearchDraft]:
    """Generate draft using Claude"""
    try:
        client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

        prompt = _build_publishable_outline_prompt(request, literature_context)

        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=8000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.content[0].text
        return _parse_structured_ai_response(content, fallback_title=request.idea)

    except Exception as e:
        print(f"Claude generation failed: {e}")
        return None


def _generate_with_volcengine(request: ResearchIdeaRequest, literature_context: str = "") -> Optional[ResearchDraft]:
    """Generate draft using Volcengine (鐏北寮曟搸)"""
    try:
        api_key = ''.join((os.getenv('VOLCENGINE_API_KEY') or os.getenv('ARK_API_KEY') or '').split())
        model_id = (os.getenv('VOLCENGINE_MODEL_ID') or os.getenv('WORKER_CLONE_MODEL') or 'doubao-lite-32k').strip()
        endpoint = (os.getenv('VOLCENGINE_ENDPOINT') or os.getenv('ARK_BASE_URL') or 'https://ark.cn-beijing.volces.com/api/v3/chat/completions').strip()
        if endpoint.rstrip('/').endswith('/api/v3'):
            endpoint = endpoint.rstrip('/') + '/chat/completions'

        prompt = _build_publishable_outline_prompt(request, literature_context)

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': model_id,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'max_tokens': 12000,
            'temperature': 0.7,
            'stream': False
        }

        response = requests.post(endpoint, headers=headers, json=payload, timeout=180)
        response.raise_for_status()

        result = response.json()
        content = result['choices'][0]['message']['content']

        return _parse_structured_ai_response(content, fallback_title=request.idea)

    except Exception as e:
        print(f"Volcengine generation failed: {e}")
        return None


def _generate_enhanced_mock_draft(request: ResearchIdeaRequest, literature_results: list = None) -> ResearchDraft:
    """Generate an enhanced mock draft that incorporates Zotero literature context in English"""
    
    base_title = f"[TEST MOCK DRAFT] {request.idea or 'Research Draft'}"
    base_abstract = """This is a test mock draft because no configured AI provider returned a usable response. It uses metadata from the selected Zotero collection to validate the local workflow, file export, and bibliography generation. It should not be treated as a final academic manuscript."""
    
    base_introduction = f"""The proposed study addresses the research topic "{request.idea}" within the field of {request.field}. This mock draft is generated only to validate the local workflow when the configured AI provider is unavailable. The introduction should be replaced by a real model-generated narrative before academic use."""
    
    # Generate literature review based on actual Zotero items in English
    literature_review = "Existing research from the selected or supplemental literature set provides the following starting context:\n\n"
    if literature_results:
        for i, item in enumerate(literature_results[:5]):
            title = item.get('title', 'Related Research')
            authors = ', '.join(item.get('authors', [])[:2]) if item.get('authors') else 'Researchers'
            year = item.get('year', 'Recent')[:4] if item.get('year') else 'Recent'
            literature_review += f"{i+1}. {authors} ({year}) in '{title[:50]}...' explored related technical methods, providing important references for this study.\n"
    else:
        literature_review += """1. Su and Boonham (2025) in spectral imaging technology for weed detection research, providing a technical foundation for multispectral disease detection.
2. Related research shows that nitrogen management affects crop productivity and is closely related to disease occurrence.
3. Machine learning applications in agricultural monitoring have become a research hotspot.
4. The potential of remote sensing technology in early crop disease detection is being widely explored."""
    
    data_context = request.data_description or "The user has not provided detailed dataset information."
    base_methodology = f"""Data context: {data_context}

This mock methods section should be replaced by the AI-generated draft. A conservative implementation plan would first construct model-ready features from the user-described data, then train and validate a topic-appropriate predictive model against held-out observations. The generated demo_data.py and demo_method.py files are intended only as scaffolds."""
    
    base_results = """This mock draft does not report real experimental results. Expected results should be generated by the configured AI model and then revised after code execution and data analysis."""
    
    base_conclusion = """This mock conclusion only confirms that the local file-generation workflow is operating. It should not be treated as scientific content."""
    
    # Generate references based on Zotero items in English format
    references = []
    if literature_results:
        for item in literature_results[:8]:
            title = item.get('title', 'Research Paper')
            authors = item.get('authors', [])
            year = item.get('year', '2024')[:4] if item.get('year') else '2024'
            
            # Format as academic reference
            if not authors:
                ref = f"Author Unknown. ({year}). {title}."
            elif len(authors) == 1:
                ref = f"{authors[0]}. ({year}). {title}."
            elif len(authors) == 2:
                ref = f"{authors[0]} & {authors[1]}. ({year}). {title}."
            else:
                ref = f"{authors[0]} et al. ({year}). {title}."
            
            references.append(ref)
    else:
        references = [
            "Workflow Test Reference. (2026). Placeholder reference used only when no Zotero or external literature metadata is available.",
            "Metadata Validation Reference. (2026). Placeholder reference for testing bibliography export and citation rendering.",
            "Draft Generation Reference. (2026). Placeholder reference for validating local Markdown, LaTeX, and PDF generation."
        ]
    
    return ResearchDraft(
        title=base_title,
        abstract=base_abstract,
        introduction=base_introduction,
        literature_review=literature_review,
        methodology=base_methodology,
        expected_results=base_results,
        conclusion=base_conclusion,
        references=references,
        generated_at=datetime.utcnow().isoformat() + 'Z',
        word_count=2800,
        source_items=literature_results or []
    )


def _parse_structured_ai_response(content: str, fallback_title: str = 'Untitled Research Draft') -> ResearchDraft:
    """Parse an English AI response into a ResearchDraft structure."""
    sections: dict[str, Any] = {}
    current_section = None
    header_patterns = {
        'title': r'^(#\s*)?(1\.\s*)?Title\s*:?\s*',
        'abstract': r'^(#+\s*)?(2\.\s*)?Abstract\s*:?\s*$',
        'introduction': r'^(#+\s*)?((1|3)\.\s*)?Introduction\s*:?\s*$',
        'literature_review': r'^(#+\s*)?((2|4)\.\s*)?(Literature Synthesis Before Writing|Literature Review)\s*:?\s*$',
        'methodology': r'^(#+\s*)?((3|5)\.\s*)?(Data|Methods|Data and Methodology|Methodology)\s*:?\s*$',
        'expected_results': r'^(#+\s*)?((4|6)\.\s*)?(Expected Results|Results)\s*:?\s*$',
        'conclusion': r'^(#+\s*)?((5|7)\.\s*)?(Discussion|Conclusion)\s*:?\s*$',
        'references': r'^(#+\s*)?((6|8)\.\s*)?References\s*:?\s*$',
    }

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        matched_section = None
        for section_name, pattern in header_patterns.items():
            if re.match(pattern, line, re.IGNORECASE):
                matched_section = section_name
                break

        if matched_section:
            current_section = matched_section
            if matched_section == 'references':
                sections.setdefault('references', [])
            elif matched_section == 'title':
                title = re.sub(header_patterns['title'], '', line, flags=re.IGNORECASE).lstrip(':').strip()
                sections['title'] = title
            else:
                if matched_section in sections and sections.get(matched_section):
                    sections[matched_section] = sections.get(matched_section, '').rstrip() + '\n\n'
                else:
                    sections[matched_section] = ''
            continue

        if line.startswith('# '):
            candidate_title = line.lstrip('#').strip()
            if candidate_title and 'author=' not in candidate_title.lower() and '```' not in candidate_title:
                sections.setdefault('title', candidate_title)
                current_section = None
                continue

        if current_section == 'references':
            if line.startswith('-') or line[0].isdigit() or '@' in line:
                sections.setdefault('references', []).append(line.lstrip('0123456789.- '))
        elif current_section == 'title':
            if not sections.get('title'):
                sections['title'] = line
        elif current_section:
            sections[current_section] = sections.get(current_section, '') + line + ' '

    return ResearchDraft(
        title=sections.get('title', '').strip() or fallback_title,
        abstract=sections.get('abstract', '').strip(),
        introduction=sections.get('introduction', '').strip(),
        literature_review=sections.get('literature_review', '').strip(),
        methodology=sections.get('methodology', '').strip(),
        expected_results=sections.get('expected_results', '').strip(),
        conclusion=sections.get('conclusion', '').strip(),
        references=sections.get('references', []),
        generated_at=datetime.utcnow().isoformat() + 'Z',
        word_count=len(content.split()),
        raw_content=content,
    )


def _parse_ai_response(content: str) -> ResearchDraft:
    """Parse a plain-text AI response into a ResearchDraft fallback structure."""
    heading_map = {
        'abstract': 'abstract',
        'literature synthesis before writing': 'literature_review',
        'literature review': 'literature_review',
        'introduction': 'introduction',
        'data': 'introduction',
        'methods': 'methodology',
        'methodology': 'methodology',
        'results': 'expected_results',
        'expected results': 'expected_results',
        'figure and table plan': 'expected_results',
        'discussion': 'conclusion',
        'conclusion': 'conclusion',
        'references': 'references',
    }
    sections: dict[str, Any] = {'references': []}
    current_section: str | None = None

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        normalized = re.sub(r'^[#\d\.\s-]+', '', line).strip().lower().rstrip(':')
        if normalized in heading_map:
            current_section = heading_map[normalized]
            if current_section != 'references':
                sections.setdefault(current_section, '')
            continue
        if line.startswith('# '):
            sections.setdefault('title', line.lstrip('#').strip())
            current_section = None
            continue
        if current_section == 'references':
            if line.startswith('-') or line[:1].isdigit() or '@' in line:
                sections.setdefault('references', []).append(line.lstrip('0123456789.- '))
        elif current_section:
            sections[current_section] = (sections.get(current_section, '') + ' ' + line).strip()

    return ResearchDraft(
        title=sections.get('title', '').strip() or 'Untitled Research Draft',
        abstract=sections.get('abstract', '').strip(),
        introduction=sections.get('introduction', '').strip(),
        literature_review=sections.get('literature_review', '').strip(),
        methodology=sections.get('methodology', '').strip(),
        expected_results=sections.get('expected_results', '').strip(),
        conclusion=sections.get('conclusion', '').strip(),
        references=sections.get('references', []),
        generated_at=datetime.utcnow().isoformat() + 'Z',
        word_count=len(content.split()),
        raw_content=content,
    )
def process_research_request(data: dict[str, Any]) -> dict[str, Any]:
    """Process a frontend request using the selected literature source."""
    request = ResearchIdeaRequest(
        idea=data.get('idea', '').strip(),
        field=data.get('field', '').strip(),
        journal=data.get('journal', None),
        output_format=data.get('output_format', 'tex'),
        add_to_zotero=data.get('add_to_zotero', False),
        email=data.get('email', '').strip(),
        collection=(data.get('collection') or '').strip() or None,
        data_description=(data.get('data_description') or '').strip() or None,
        literature_mode=(data.get('literature_mode') or 'zotero').strip().lower(),
    )

    if not request.idea or not request.field or not request.email:
        return {
            'status': 'error',
            'message': 'Research topic, field, and email are required.',
        }

    if request.literature_mode not in {'zotero', 'external'}:
        return {
            'status': 'error',
            'message': 'Invalid literature mode. Use "zotero" or "external".',
        }

    if request.literature_mode == 'zotero' and not request.collection:
        return {
            'status': 'error',
            'message': 'Please select a Zotero collection. Draft generation only uses literature from the selected collection.',
        }

    submission_id = f"sub_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(request.idea) % 10000:04d}"
    draft = generate_research_draft(request, submission_id=submission_id)
    if not draft:
        return {
            'status': 'error',
            'message': (
                f'No usable literature was found for literature mode "{request.literature_mode}". '
                'For Zotero mode, verify the selected collection. For external mode, check network access '
                'to Semantic Scholar/arXiv/Crossref or try a more specific English topic/data description.'
            ),
        }

    draft.source_items = _annotate_citation_positions(draft.source_items or [], draft)
    draft.literature_summary_files = _save_literature_summaries(
        draft.source_items or [],
        submission_id,
        idea=request.idea,
    )
    zotero_imported_keys = []
    supplemental_items = [
        item for item in (draft.source_items or [])
        if item.get('reference_origin') == 'supplemental_external'
    ]
    if request.add_to_zotero and request.literature_mode == 'zotero' and supplemental_items:
        zotero_imported_keys = sync_literature_items_to_zotero(
            supplemental_items,
            collection_name=request.collection or f"ResearchDraft.ai {submission_id}",
        )
    file_paths = _save_draft_to_file(draft, request.output_format, submission_id, request=request)
    quality_report = _load_quality_report_from_files(file_paths)
    submission = {
        'id': submission_id,
        'idea': request.idea,
        'field': request.field,
        'data_description': request.data_description,
        'journal': request.journal,
        'collection': request.collection,
        'literature_mode': request.literature_mode,
        'output_format': request.output_format,
        'add_to_zotero': request.add_to_zotero,
        'email': request.email,
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'status': 'completed',
        'draft_files': file_paths,
        'draft_title': draft.title,
        'word_count': draft.word_count,
        'source_count': len(draft.source_items or []),
        'literature_summary_files': draft.literature_summary_files or [],
        'zotero_imported_keys': zotero_imported_keys,
        'supplemental_source_count': len(supplemental_items),
        'quality_report_file': file_paths.get('quality_report'),
        'quality_status': quality_report.get('status'),
        'quality_error_count': quality_report.get('error_count'),
        'quality_warning_count': quality_report.get('warning_count'),
    }

    submissions = _load_submissions()
    submissions.append(submission)
    _save_submissions(submissions)

    return {
        'status': 'success',
        'message': (
            f"Research draft generated using {'Zotero collection plus automatic supplements' if request.literature_mode == 'zotero' else 'external scholarly search'}. "
            f"Title: {draft.title}."
        ),
        'submission_id': submission_id,
        'draft': {
            'title': draft.title,
            'abstract': draft.abstract,
            'introduction': draft.introduction,
            'literature_review': draft.literature_review,
            'methodology': draft.methodology,
            'expected_results': draft.expected_results,
            'conclusion': draft.conclusion,
            'references': draft.references,
            'generated_at': draft.generated_at,
            'word_count': draft.word_count,
            'raw_content': draft.raw_content,
            'files': file_paths,
            'literature_summary_files': draft.literature_summary_files or [],
            'zotero_imported_count': len(zotero_imported_keys),
            'supplemental_source_count': len(supplemental_items),
            'source_count': len(draft.source_items or []),
            'literature_mode': request.literature_mode,
            'quality': {
                'status': quality_report.get('status'),
                'error_count': quality_report.get('error_count'),
                'warning_count': quality_report.get('warning_count'),
                'issues': quality_report.get('issues', []),
            },
        },
    }


def get_draft_files(submission_id: str) -> Dict[str, str]:
    """Get draft files for a submission."""
    submissions = _load_submissions()
    for submission in submissions:
        if submission.get('id') == submission_id:
            return submission.get('draft_files', {})
    return {}


def get_draft_content(file_path: str) -> Optional[str]:
    """Get content of a draft file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading draft file {file_path}: {e}")
        return None


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
