from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET
from typing import Any

import requests

from export.bibtex import extract_year
from models import ResearchIdeaRequest


def search_external_literature(query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Search external scholarly sources for supplemental references."""
    results = search_semantic_scholar(query, limit=limit)

    if len(results) < limit:
        arxiv_results = search_arxiv_literature(query, limit=limit - len(results))
        results.extend(dedupe_supplemental_items(results, arxiv_results))

    if len(results) < limit:
        crossref_results = search_crossref_literature(query, limit=limit - len(results))
        results.extend(dedupe_supplemental_items(results, crossref_results))

    if os.getenv("SERPAPI_API_KEY") and len(results) < limit:
        serpapi_results = search_serpapi_google_scholar(query, limit=limit - len(results))
        results.extend(dedupe_supplemental_items(results, serpapi_results))

    if len(results) < limit and ("agn" in query.lower() or "active galactic" in query.lower()):
        fallback_query = "active galactic nuclei variability outburst prediction machine learning time-domain survey"
        fallback_results = search_semantic_scholar(fallback_query, limit=limit - len(results))
        results.extend(dedupe_supplemental_items(results, fallback_results))

    return results[:limit]


def external_query_tokens(query: str, limit: int = 8) -> list[str]:
    stopwords = {
        "using", "based", "with", "from", "data", "model", "models", "study",
        "research", "catalog", "catalogs", "files", "image", "images",
    }
    tokens = []
    lowered_tokens = set()
    for token in re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", query or ""):
        lowered = token.lower()
        if lowered not in stopwords and lowered not in lowered_tokens:
            tokens.append(token)
            lowered_tokens.add(lowered)
        if len(tokens) >= limit:
            break
    return tokens


def search_arxiv_literature(query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Search arXiv metadata as a no-key fallback."""
    tokens = external_query_tokens(query, limit=6)
    if not tokens:
        return []
    arxiv_query = " AND ".join(f"all:{token}" for token in tokens[:5])
    try:
        response = requests.get(
            "https://export.arxiv.org/api/query",
            params={
                "search_query": arxiv_query,
                "start": 0,
                "max_results": min(limit, 20),
                "sortBy": "relevance",
                "sortOrder": "descending",
            },
            timeout=30,
        )
        response.raise_for_status()
        root = ET.fromstring(response.text)
    except Exception as exc:
        print(f"arXiv search failed: {exc}")
        return []

    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    formatted = []
    for entry in root.findall("atom:entry", ns):
        title = " ".join((entry.findtext("atom:title", default="", namespaces=ns) or "").split())
        summary = " ".join((entry.findtext("atom:summary", default="", namespaces=ns) or "").split())
        published = entry.findtext("atom:published", default="", namespaces=ns) or ""
        url = entry.findtext("atom:id", default="", namespaces=ns) or ""
        authors = [
            (author.findtext("atom:name", default="", namespaces=ns) or "").strip()
            for author in entry.findall("atom:author", ns)
        ]
        categories = [cat.attrib.get("term", "") for cat in entry.findall("atom:category", ns)]
        formatted.append({
            "key": url.rsplit("/", 1)[-1] or title,
            "title": title,
            "authors": [author for author in authors if author],
            "abstract": summary,
            "year": published[:4],
            "itemType": "journalArticle",
            "url": url,
            "pdf_url": url.replace("/abs/", "/pdf/") if "/abs/" in url else "",
            "tags": categories,
            "doi": "",
            "publication": "arXiv",
            "volume": "",
            "issue": "",
            "pages": "",
            "publisher": "",
            "citation_count": 0,
            "influential_citation_count": 0,
            "source": "arxiv",
            "reference_origin": "supplemental_external",
        })
    return clean_literature_items(formatted, query)


def search_crossref_literature(query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Search Crossref metadata as a no-key fallback."""
    if not query:
        return []
    try:
        response = requests.get(
            "https://api.crossref.org/works",
            params={
                "query.bibliographic": query,
                "rows": min(limit, 20),
                "select": "DOI,title,author,container-title,published-print,published-online,issued,URL,is-referenced-by-count,abstract,type,page,volume,issue",
            },
            headers={"User-Agent": "ResearchDraft.ai local MVP (mailto:test@example.com)"},
            timeout=30,
        )
        response.raise_for_status()
        works = (response.json().get("message") or {}).get("items", [])
    except Exception as exc:
        print(f"Crossref search failed: {exc}")
        return []

    formatted = []
    for work in works:
        title = " ".join((work.get("title") or [""])[0].split())
        container = " ".join((work.get("container-title") or [""])[0].split())
        authors = []
        for author in work.get("author") or []:
            name = " ".join([author.get("given", ""), author.get("family", "")]).strip()
            if name:
                authors.append(name)
        date_parts = (
            ((work.get("published-print") or {}).get("date-parts") or [[]])[0]
            or ((work.get("published-online") or {}).get("date-parts") or [[]])[0]
            or ((work.get("issued") or {}).get("date-parts") or [[]])[0]
        )
        year = str(date_parts[0]) if date_parts else ""
        abstract = re.sub(r"<[^>]+>", " ", work.get("abstract") or "")
        formatted.append({
            "key": work.get("DOI") or title,
            "title": title,
            "authors": authors,
            "abstract": " ".join(abstract.split()),
            "year": year,
            "itemType": "journalArticle",
            "url": work.get("URL", ""),
            "pdf_url": "",
            "tags": [],
            "doi": work.get("DOI", ""),
            "publication": container,
            "volume": work.get("volume", ""),
            "issue": work.get("issue", ""),
            "pages": work.get("page", ""),
            "publisher": "",
            "citation_count": work.get("is-referenced-by-count") or 0,
            "influential_citation_count": 0,
            "source": "crossref",
            "reference_origin": "supplemental_external",
        })
    return clean_literature_items(formatted, query)


def normalize_reference_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (title or "").lower()).strip()


def fallback_external_abstract(item: dict[str, Any], query: str = "") -> str:
    title = item.get("title") or "Untitled scholarly record"
    publication = item.get("publication") or item.get("source") or "an external scholarly index"
    year = extract_year(item.get("year", ""))
    query_hint = f" The record was retrieved for the query context: {query}." if query else ""
    return (
        "No abstract was returned by the metadata API for this paper. The available metadata identifies "
        f"'{title}' as a {year} scholarly record associated with {publication}.{query_hint} "
        "Use this item conservatively and verify the full paper before relying on detailed claims."
    )


def clean_literature_items(items: list[dict[str, Any]], query: str = "") -> list[dict[str, Any]]:
    """Remove unusable records and guarantee enough text for downstream HTML summaries."""
    cleaned: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items or []:
        title = (item.get("title") or "").strip()
        if not title:
            continue
        key = (item.get("doi") or normalize_reference_title(title)).lower()
        if not key or key in seen:
            continue
        seen.add(key)
        copy = dict(item)
        copy["title"] = title
        copy["abstract"] = (copy.get("abstract") or "").strip() or fallback_external_abstract(copy, query)
        copy["authors"] = [author for author in (copy.get("authors") or []) if author]
        copy["publication"] = (copy.get("publication") or copy.get("venue") or copy.get("source") or "").strip()
        copy["reference_origin"] = copy.get("reference_origin") or "supplemental_external"
        cleaned.append(copy)
    return cleaned


def dedupe_supplemental_items(existing: list[dict[str, Any]], supplemental: list[dict[str, Any]]) -> list[dict[str, Any]]:
    existing_keys = {
        (item.get("doi") or normalize_reference_title(item.get("title", ""))).lower()
        for item in existing or []
        if item.get("doi") or item.get("title")
    }
    deduped = []
    for item in supplemental or []:
        key = (item.get("doi") or normalize_reference_title(item.get("title", ""))).lower()
        if not key or key in existing_keys:
            continue
        existing_keys.add(key)
        deduped.append(item)
    return deduped


def build_external_search_query(request: ResearchIdeaRequest, existing_items: list[dict[str, Any]]) -> str:
    """Create an English scholarly query for supplemental search."""
    raw_context = " ".join([
        request.idea or "",
        request.field or "",
        request.data_description or "",
        " ".join((item.get("title") or "") for item in (existing_items or [])[:3]),
    ]).lower()

    if "agn" in raw_context or "active galactic" in raw_context:
        return "active galactic nuclei machine learning variability time-domain"
    if any(term in raw_context for term in ["potato", "disease", "plant disease"]):
        return "potato disease early detection multimodal remote sensing machine learning UAV Sentinel-2 plant disease transformer"

    tokens = [
        token for token in re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", raw_context)
        if token.lower() not in {
            "the", "and", "for", "with", "using", "based", "data", "study",
            "research", "method", "model", "models", "analysis",
        }
    ]
    deduped = list(dict.fromkeys(tokens))
    return " ".join(deduped[:18]) or request.idea


def search_semantic_scholar(query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Search Semantic Scholar Graph API for paper metadata."""
    if not query:
        return []

    endpoint = "https://api.semanticscholar.org/graph/v1/paper/search"
    fields = ",".join([
        "title",
        "abstract",
        "year",
        "authors",
        "venue",
        "publicationVenue",
        "citationCount",
        "influentialCitationCount",
        "externalIds",
        "url",
        "openAccessPdf",
    ])
    headers = {}
    if os.getenv("SEMANTIC_SCHOLAR_API_KEY"):
        headers["x-api-key"] = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")

    try:
        response = requests.get(
            endpoint,
            params={"query": query, "limit": min(limit, 100), "fields": fields},
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        papers = response.json().get("data", [])
    except Exception as exc:
        print(f"Semantic Scholar search failed: {exc}")
        return []

    formatted = []
    for paper in papers:
        external_ids = paper.get("externalIds") or {}
        publication_venue = paper.get("publicationVenue") or {}
        formatted.append({
            "key": paper.get("paperId") or external_ids.get("DOI") or paper.get("title", ""),
            "title": paper.get("title", ""),
            "authors": [author.get("name", "") for author in paper.get("authors", []) if author.get("name")],
            "abstract": paper.get("abstract") or "",
            "year": str(paper.get("year") or ""),
            "itemType": "journalArticle",
            "url": paper.get("url") or (paper.get("openAccessPdf") or {}).get("url", ""),
            "pdf_url": (paper.get("openAccessPdf") or {}).get("url", ""),
            "tags": [],
            "doi": external_ids.get("DOI", ""),
            "publication": publication_venue.get("name") or paper.get("venue", ""),
            "volume": "",
            "issue": "",
            "pages": "",
            "publisher": "",
            "citation_count": paper.get("citationCount") or 0,
            "influential_citation_count": paper.get("influentialCitationCount") or 0,
            "source": "semantic_scholar",
            "reference_origin": "supplemental_external",
        })
    return clean_literature_items(formatted, query)


def search_serpapi_google_scholar(query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Search Google Scholar through SerpApi when configured."""
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key or not query:
        return []

    try:
        response = requests.get(
            "https://serpapi.com/search.json",
            params={
                "engine": "google_scholar",
                "q": query,
                "api_key": api_key,
                "num": min(limit, 20),
            },
            timeout=30,
        )
        response.raise_for_status()
        papers = response.json().get("organic_results", [])
    except Exception as exc:
        print(f"SerpApi Google Scholar search failed: {exc}")
        return []

    formatted = []
    for index, paper in enumerate(papers[:limit]):
        publication_info = paper.get("publication_info") or {}
        authors = [
            author.get("name", "")
            for author in publication_info.get("authors", [])
            if author.get("name")
        ]
        snippet = paper.get("snippet") or ""
        year = ""
        year_match = re.search(r"(19|20)\d{2}", publication_info.get("summary", "") + " " + snippet)
        if year_match:
            year = year_match.group(0)
        formatted.append({
            "key": paper.get("result_id") or f"serpapi_{index}",
            "title": paper.get("title", ""),
            "authors": authors,
            "abstract": snippet,
            "year": year,
            "itemType": "journalArticle",
            "url": paper.get("link", ""),
            "pdf_url": "",
            "tags": [],
            "doi": "",
            "publication": publication_info.get("summary", ""),
            "volume": "",
            "issue": "",
            "pages": "",
            "publisher": "",
            "citation_count": int((paper.get("inline_links") or {}).get("cited_by", {}).get("total", 0) or 0),
            "influential_citation_count": 0,
            "source": "google_scholar_serpapi",
            "reference_origin": "supplemental_external",
        })
    return clean_literature_items(formatted, query)

