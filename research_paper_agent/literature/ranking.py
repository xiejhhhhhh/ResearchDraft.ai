from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Optional

import requests

from config import DATA_DIR


EASYSCHOLAR_CACHE_FILE = DATA_DIR / "easyscholar_cache.json"


def tokenize_for_relevance(text: str) -> set[str]:
    stopwords = {
        "the", "and", "for", "with", "using", "during", "early", "study", "research",
        "paper", "method", "methods", "data", "model", "models", "analysis", "based",
    }
    return {
        token
        for token in re.findall(r"[a-zA-Z][a-zA-Z0-9-]{2,}", (text or "").lower())
        if token not in stopwords
    }


def _load_easyscholar_cache() -> dict[str, Any]:
    if not EASYSCHOLAR_CACHE_FILE.exists():
        return {}
    try:
        with EASYSCHOLAR_CACHE_FILE.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return {}


def _save_easyscholar_cache(cache: dict[str, Any]) -> None:
    EASYSCHOLAR_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with EASYSCHOLAR_CACHE_FILE.open("w", encoding="utf-8") as handle:
        json.dump(cache, handle, ensure_ascii=False, indent=2)


def rank_text_to_score(rank_text: str) -> float:
    rank = (rank_text or "").strip().upper()
    if not rank:
        return 0.0
    if rank in {"TOP", "T", "Q1", "A+", "AA", "A*"}:
        return 1.0
    if rank in {"A", "Q2"}:
        return 0.85
    if rank in {"B+", "B", "Q3"}:
        return 0.65
    if rank in {"C", "Q4"}:
        return 0.4
    if rank in {"D", "E"}:
        return 0.2
    if re.fullmatch(r"[1-5]", rank):
        return {"1": 1.0, "2": 0.8, "3": 0.6, "4": 0.4, "5": 0.2}[rank]
    return 0.0


def custom_rank_number_to_text(rank_info: list[dict[str, Any]], encoded_rank: str) -> Optional[str]:
    try:
        uuid, rank_number = encoded_rank.split("&&&", 1)
    except ValueError:
        return None
    info = next((item for item in rank_info if item.get("uuid") == uuid), None)
    if not info:
        return None
    key_map = {
        "1": "oneRankText",
        "2": "twoRankText",
        "3": "threeRankText",
        "4": "fourRankText",
        "5": "fiveRankText",
    }
    return info.get(key_map.get(rank_number.strip(), ""))


def parse_easyscholar_rank(raw: dict[str, Any]) -> dict[str, Any]:
    """Convert EasyScholar rank payload into normalized score metadata."""
    data = raw.get("data") or {}
    official = (data.get("officialRank") or {}).get("all") or {}
    custom = data.get("customRank") or {}
    rank_info = custom.get("rankInfo") or []
    custom_ranks = custom.get("rank") or []

    labels = []
    scores = []
    for dataset, rank_text in official.items():
        score = rank_text_to_score(str(rank_text))
        if score:
            labels.append(f"{dataset}:{rank_text}")
            scores.append(score)

    for encoded_rank in custom_ranks:
        rank_text = custom_rank_number_to_text(rank_info, encoded_rank)
        if rank_text:
            score = rank_text_to_score(str(rank_text))
            if score:
                labels.append(f"custom:{rank_text}")
                scores.append(score)

    score = max(scores) if scores else 0.0
    return {
        "journal_score": round(score, 3),
        "journal_rank_labels": labels[:12],
        "has_easyscholar_result": bool(labels),
    }


def get_easyscholar_publication_rank(publication_name: str) -> dict[str, Any]:
    """Fetch and cache EasyScholar rank metadata for a publication name."""
    publication = (publication_name or "").strip()
    if not publication:
        return {"journal_score": 0.0, "journal_rank_labels": [], "has_easyscholar_result": False}

    cache_key = publication.lower()
    cache = _load_easyscholar_cache()
    if cache_key in cache:
        return cache[cache_key]

    secret_key = (os.getenv("EASYSCHOLAR_SECRET_KEY") or "").strip()
    if not secret_key:
        result = {"journal_score": 0.0, "journal_rank_labels": [], "has_easyscholar_result": False}
        cache[cache_key] = result
        _save_easyscholar_cache(cache)
        return result

    try:
        response = requests.get(
            "https://www.easyscholar.cc/open/getPublicationRank",
            params={"secretKey": secret_key, "publicationName": publication},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        result = parse_easyscholar_rank(payload) if payload.get("code") == 200 else {
            "journal_score": 0.0,
            "journal_rank_labels": [],
            "has_easyscholar_result": False,
        }
    except Exception as exc:
        print(f"EasyScholar lookup failed for '{publication}': {exc}")
        result = {"journal_score": 0.0, "journal_rank_labels": [], "has_easyscholar_result": False}

    cache[cache_key] = result
    _save_easyscholar_cache(cache)
    return result


def weight_literature_items(items: list[dict[str, Any]], idea: str, journal: Optional[str] = None) -> list[dict[str, Any]]:
    """Assign a citation weight using relevance, citations, and EasyScholar journal rank."""
    idea_terms = tokenize_for_relevance(idea)
    weighted = []
    for item in items:
        title_terms = tokenize_for_relevance(item.get("title", ""))
        abstract_terms = tokenize_for_relevance(item.get("abstract", ""))
        item_terms = title_terms | abstract_terms
        overlap = len(idea_terms & item_terms)
        relevance = overlap / max(len(idea_terms), 1)

        citation_count = int(item.get("citation_count") or 0)
        influential_count = int(item.get("influential_citation_count") or 0)
        citation_authority = min(1.0, (citation_count / 300.0) + (influential_count / 100.0))

        publication = (item.get("publication") or "").lower()
        target_journal = (journal or "").lower()
        venue_bonus = 0.15 if target_journal and target_journal in publication else 0.0
        journal_rank = get_easyscholar_publication_rank(item.get("publication", ""))
        journal_score = float(journal_rank.get("journal_score") or 0.0)
        authority = round((0.45 * citation_authority) + (0.55 * journal_score), 3)
        weight = round((0.55 * relevance) + (0.30 * authority) + venue_bonus + 0.10, 3)

        copy = dict(item)
        copy["relevance_score"] = round(relevance, 3)
        copy["authority_score"] = round(authority, 3)
        copy["citation_authority_score"] = round(citation_authority, 3)
        copy["journal_score"] = round(journal_score, 3)
        copy["journal_rank_labels"] = journal_rank.get("journal_rank_labels", [])
        copy["citation_weight"] = min(weight, 1.0)
        weighted.append(copy)

    weighted.sort(key=lambda item: item.get("citation_weight", 0), reverse=True)
    return weighted

