from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from pyzotero import zotero


def get_zotero_client():
    """Initialize and return Zotero client without exposing credentials."""
    library_id = os.getenv("ZOTERO_LIBRARY_ID")
    api_key = os.getenv("ZOTERO_API_KEY")
    library_type = os.getenv("ZOTERO_LIBRARY_TYPE", "user")
    if not library_id or not api_key:
        return None

    try:
        return zotero.Zotero(library_id, library_type, api_key)
    except Exception as exc:
        print(f"Failed to initialize Zotero client: {exc}")
        return None


def find_collection_key(client, collection_name: str) -> Optional[str]:
    """Find a Zotero collection key by name, using case-insensitive and substring matching."""
    if not collection_name:
        return None

    try:
        name_lower = collection_name.strip().lower()
        collections = client.collections()

        for coll in collections:
            coll_name = coll["data"].get("name", "").strip().lower()
            if coll_name == name_lower:
                return coll["key"]

        for coll in collections:
            coll_name = coll["data"].get("name", "").strip().lower()
            if name_lower in coll_name or coll_name in name_lower:
                return coll["key"]
    except Exception as exc:
        print(f"Error looking up collection '{collection_name}': {exc}")

    return None


def list_zotero_collections() -> list[dict[str, str]]:
    """Return Zotero collection names and keys without exposing credentials."""
    client = get_zotero_client()
    if not client:
        return []

    try:
        collections = client.collections()
    except Exception as exc:
        print(f"Error listing Zotero collections: {exc}")
        return []

    return [
        {
            "key": coll.get("key", ""),
            "name": coll.get("data", {}).get("name", ""),
        }
        for coll in collections
        if coll.get("key") and coll.get("data", {}).get("name")
    ]


def get_zotero_items(client, tag: Optional[str] = None, collection: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve article-like items from Zotero library with optional tag/collection filtering."""
    if not client:
        return []

    try:
        items = []
        if collection:
            try:
                collection_key = find_collection_key(client, collection)
                if collection_key:
                    items = client.collection_items(collection_key, limit=limit)
                else:
                    print(f"Collection '{collection}' not found, returning empty results")
                    items = []
            except Exception as exc:
                print(f"Error accessing collection '{collection}': {exc}")
                items = []
        elif tag:
            items = client.items(tag=tag, limit=limit)
        else:
            items = client.items(limit=limit)

        formatted_items = []
        for item in items:
            data = item.get("data", {})
            item_type = data.get("itemType", "")
            if item_type in {"attachment", "note", "annotation"} or data.get("parentItem"):
                continue
            if not data.get("title", "").strip():
                continue
            formatted_items.append({
                "key": item["key"],
                "title": data.get("title", ""),
                "authors": [
                    f"{creator.get('firstName', '')} {creator.get('lastName', '')}".strip()
                    for creator in data.get("creators", [])
                    if creator.get("creatorType") == "author"
                ],
                "abstract": data.get("abstractNote", ""),
                "year": data.get("date", ""),
                "itemType": item_type,
                "url": data.get("url", ""),
                "tags": [tag_dict["tag"] for tag_dict in data.get("tags", [])],
                "doi": data.get("DOI", ""),
                "publication": data.get("publicationTitle", ""),
                "volume": data.get("volume", ""),
                "issue": data.get("issue", ""),
                "pages": data.get("pages", ""),
                "publisher": data.get("publisher", ""),
                "reference_origin": "existing_zotero",
            })

        return formatted_items

    except Exception as exc:
        print(f"Zotero retrieval failed: {exc}")
        return []


def add_to_zotero(client, item_data: Dict[str, Any], collection: Optional[str] = None) -> Optional[str]:
    """Add an item to Zotero library."""
    if not client:
        return None

    try:
        response = client.create_items([item_data])
        if response["successful"]:
            item_key = list(response["successful"].keys())[0]
            if collection:
                collection_key = get_or_create_collection(client, collection)
                if collection_key:
                    client.addto_collection(collection_key, [item_key])
            return item_key

        print(f"Failed to create Zotero item: {response['failed']}")
        return None
    except Exception as exc:
        print(f"Adding to Zotero failed: {exc}")
        return None


def zotero_item_from_literature(item: dict[str, Any]) -> dict[str, Any]:
    creators = []
    for author in item.get("authors") or []:
        parts = author.split()
        creators.append({
            "creatorType": "author",
            "firstName": " ".join(parts[:-1]) if len(parts) > 1 else "",
            "lastName": parts[-1] if parts else author,
        })
    return {
        "itemType": "journalArticle",
        "title": item.get("title", ""),
        "creators": creators,
        "abstractNote": item.get("abstract", ""),
        "publicationTitle": item.get("publication", ""),
        "date": item.get("year", ""),
        "DOI": item.get("doi", ""),
        "url": item.get("url", ""),
        "tags": [{"tag": "ResearchDraft.ai"}, {"tag": item.get("source", "external")}],
    }


def sync_literature_items_to_zotero(items: list[dict[str, Any]], collection_name: str) -> list[str]:
    """Optionally import externally searched literature into Zotero."""
    client = get_zotero_client()
    if not client:
        return []

    created = []
    for item in items:
        if not item.get("title"):
            continue
        key = add_to_zotero(client, zotero_item_from_literature(item), collection=collection_name)
        if key:
            created.append(key)
    return created


def get_or_create_collection(client, collection_name: str) -> Optional[str]:
    """Get or create a Zotero collection."""
    try:
        collections = client.collections()
        for collection in collections:
            if collection["data"]["name"] == collection_name:
                return collection["key"]

        response = client.create_collection({"name": collection_name})
        if response["successful"]:
            return list(response["successful"].keys())[0]

        print(f"Failed to create collection: {response['failed']}")
        return None
    except Exception as exc:
        print(f"Collection operation failed: {exc}")
        return None

