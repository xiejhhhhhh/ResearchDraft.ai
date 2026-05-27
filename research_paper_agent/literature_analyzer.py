"""Reference-level reading and synthesis for ResearchDraft.ai."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from pdf_reader import (
    download_open_access_pdf,
    download_zotero_pdf,
    extract_figure_table_captions,
    extract_sections,
    find_local_zotero_pdf,
    read_pdf_text,
)


@dataclass
class PaperSummary:
    read_status: str
    research_question: str
    data_used: str
    methods: str
    scientific_results: str
    limitations: str
    figure_table_captions: list[str]
    relevance_to_study: str


def _clean(text: str, limit: int = 1200) -> str:
    text = re.sub(r'\s+', ' ', text or '').strip()
    return text[:limit].rstrip()


def _sentences(text: str) -> list[str]:
    parts = re.split(r'(?<=[.!?])\s+', _clean(text, 10000))
    return [part.strip() for part in parts if len(part.strip()) > 35]


def _pick_sentences(text: str, keywords: list[str], fallback: str, limit: int = 3) -> str:
    chosen = []
    for sentence in _sentences(text):
        lower = sentence.lower()
        if any(
            (keyword in lower if not re.match(r'^[a-z0-9-]+$', keyword) else re.search(rf'\b{re.escape(keyword)}\b', lower))
            for keyword in keywords
        ):
            chosen.append(sentence)
        if len(chosen) >= limit:
            break
    return ' '.join(chosen) if chosen else fallback


def _method_family(text: str) -> str:
    lower = text.lower()
    families = []
    if any(term in lower for term in ['cnn', 'convolutional', 'resnet', 'efficientnet']):
        families.append('convolutional image classification')
    if any(term in lower for term in ['transformer', 'vit', 'attention']):
        families.append('transformer or attention-based modelling')
    if any(term in lower for term in ['svm', 'support vector']):
        families.append('support vector machine classification')
    if any(term in lower for term in ['random forest', 'xgboost', 'gradient boosting']):
        families.append('tree-based machine learning')
    if any(term in lower for term in ['lstm', 'gru', 'time series', 'temporal']):
        families.append('temporal sequence modelling')
    if any(term in lower for term in ['uav', 'drone', 'hyperspectral', 'multispectral', 'sentinel']):
        families.append('remote-sensing feature extraction')
    return '; '.join(families) if families else 'method family not explicit in available text'


def analyze_paper(item: dict[str, Any], full_text: str = '') -> PaperSummary:
    """Generate a structured summary from full text, or from abstract metadata."""
    title = item.get('title') or 'this paper'
    abstract = item.get('abstract') or ''
    sections = extract_sections(full_text) if full_text else {}
    text_for_analysis = '\n'.join(sections.values()) if sections else abstract
    read_status = 'full_text' if full_text else 'metadata_abstract_only'

    intro_text = sections.get('introduction') or abstract
    methods_text = sections.get('methods') or text_for_analysis
    results_text = sections.get('results') or abstract
    discussion_text = ' '.join([
        sections.get('discussion', ''),
        sections.get('limitations', ''),
        sections.get('conclusion', ''),
    ]).strip()
    figure_captions = extract_figure_table_captions(full_text)

    research_question = _pick_sentences(
        intro_text,
        ['aim', 'objective', 'purpose', 'investigate', 'detect', 'classify', 'monitor'],
        f'The paper appears to address a problem related to {title}.',
        limit=2,
    )
    data_used = _pick_sentences(
        methods_text,
        ['dataset', 'data', 'image', 'uav', 'satellite', 'sentinel', 'hyperspectral', 'multispectral', 'field', 'sample'],
        'The available text does not state the dataset clearly; check the full methods section manually.',
        limit=4,
    )
    methods = _pick_sentences(
        methods_text,
        ['model', 'method', 'algorithm', 'cnn', 'transformer', 'svm', 'classification', 'learning', 'feature'],
        f'The available text suggests { _method_family(text_for_analysis) }.',
        limit=4,
    )
    scientific_results = _pick_sentences(
        results_text + ' ' + discussion_text,
        ['accuracy', 'f1', 'fscore', 'f-score', 'result', 'performance', 'improve', 'achieved', 'score', 'scores', 'range', '%', 'detected', 'classified'],
        _clean(abstract, 700) or 'Scientific results are not recoverable from the available metadata.',
        limit=4,
    )
    limitations = _pick_sentences(
        discussion_text or text_for_analysis,
        ['limitation', 'limited', 'future', 'further', 'however', 'challenge', 'uncertain', 'generaliz', 'validation', 'constraint'],
        'No explicit limitation statement was identified in the available text.',
        limit=4,
    )
    relevance = _pick_sentences(
        text_for_analysis,
        ['potato', 'disease', 'early', 'detect', 'remote sensing', 'machine learning', 'uav', 'multispectral'],
        'Relevance should be judged from title, abstract, citation weight, and method overlap.',
        limit=3,
    )

    return PaperSummary(
        read_status=read_status,
        research_question=research_question,
        data_used=data_used,
        methods=methods,
        scientific_results=scientific_results,
        limitations=limitations,
        figure_table_captions=figure_captions,
        relevance_to_study=relevance,
    )


def analyze_literature_items(
    items: list[dict[str, Any]],
    submission_id: str,
    *,
    zotero_client: Optional[Any] = None,
    pdf_cache_dir: Optional[Path] = None,
    max_fulltext: int = 10,
) -> list[dict[str, Any]]:
    """Attach a structured ``deep_summary`` to each literature item."""
    if not items:
        return []

    cache_dir = pdf_cache_dir or Path('data') / 'pdf_cache' / submission_id
    enriched = []
    for index, item in enumerate(items):
        full_text = ''
        read_status = 'metadata_abstract_only'
        pdf_status = 'PDF reading was not attempted.'
        if zotero_client is not None and index < max_fulltext and item.get('key'):
            pdf_path, pdf_status = download_zotero_pdf(zotero_client, item['key'], cache_dir)
            if pdf_path:
                full_text = read_pdf_text(pdf_path)
                if full_text:
                    read_status = 'full_text'
                else:
                    pdf_status = 'PDF was available, but text extraction returned no usable text.'

        if not full_text and index < max_fulltext:
            local_pdf, local_status = find_local_zotero_pdf(
                parent_title=item.get('title', ''),
                attachment_title=item.get('title', ''),
            )
            if local_pdf:
                local_text = read_pdf_text(local_pdf)
                if local_text:
                    full_text = local_text
                    read_status = 'full_text'
                    pdf_status = local_status
                else:
                    pdf_status = f'{local_status} Text extraction returned no usable text.'

        if not full_text and index < max_fulltext:
            oa_pdf, oa_status = download_open_access_pdf(item, cache_dir)
            if oa_pdf:
                oa_text = read_pdf_text(oa_pdf)
                if oa_text:
                    full_text = oa_text
                    read_status = 'full_text_open_access'
                    pdf_status = oa_status
                else:
                    pdf_status = f'{oa_status} Text extraction returned no usable text.'
            elif oa_status:
                pdf_status = oa_status

        summary = analyze_paper(item, full_text=full_text)
        summary.read_status = read_status
        copied = dict(item)
        copied['deep_summary'] = {
            'read_status': summary.read_status,
            'pdf_status': pdf_status,
            'research_question': summary.research_question,
            'data_used': summary.data_used,
            'methods': summary.methods,
            'scientific_results': summary.scientific_results,
            'limitations': summary.limitations,
            'figure_table_captions': summary.figure_table_captions,
            'relevance_to_study': summary.relevance_to_study,
        }
        enriched.append(copied)
    return enriched


def synthesize_cross_literature(items: list[dict[str, Any]]) -> dict[str, str]:
    """Summarize shared limitations and method/data patterns across papers."""
    summaries = [item.get('deep_summary') or {} for item in items]
    data_lines = [summary.get('data_used', '') for summary in summaries if summary.get('data_used')]
    method_lines = [summary.get('methods', '') for summary in summaries if summary.get('methods')]
    limitation_lines = [summary.get('limitations', '') for summary in summaries if summary.get('limitations')]
    result_lines = [summary.get('scientific_results', '') for summary in summaries if summary.get('scientific_results')]

    return {
        'data_patterns': _clean(' '.join(data_lines), 1800) or 'No shared data pattern was extracted.',
        'method_patterns': _clean(' '.join(method_lines), 1800) or 'No shared method pattern was extracted.',
        'limitation_patterns': _clean(' '.join(limitation_lines), 1800) or 'No explicit shared limitation pattern was extracted.',
        'result_patterns': _clean(' '.join(result_lines), 1800) or 'No shared result pattern was extracted.',
    }
