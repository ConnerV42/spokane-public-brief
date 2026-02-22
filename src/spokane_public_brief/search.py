"""Simple search over DynamoDB agenda items.

Queries all items via the type-date GSI and does keyword/relevance matching
in-memory. No external vector DB needed.

For a future upgrade: store embeddings as a list[float] attribute in DynamoDB
and compute cosine similarity in Lambda.
"""

from typing import Optional

from spokane_public_brief.models.dynamodb import query_all_agenda_items


def _score_item(item: dict, query: str) -> float:
    """Score an item against a search query using simple text matching."""
    query_lower = query.lower()
    terms = query_lower.split()
    score = 0.0

    # Fields to search with weights
    fields = [
        ("title", 3.0),
        ("summary", 2.0),
        ("why_it_matters", 1.5),
        ("topic", 1.0),
    ]

    for field, weight in fields:
        value = str(item.get(field, "")).lower()
        for term in terms:
            if term in value:
                score += weight

    # Boost by key_details matches
    details = item.get("key_details", [])
    if isinstance(details, list):
        details_text = " ".join(str(d) for d in details).lower()
        for term in terms:
            if term in details_text:
                score += 1.0

    # Normalize by number of terms
    if terms:
        score /= len(terms)

    return score


def search(query: str, top_k: int = 10, min_score: float = 0.1) -> list[dict]:
    """Search agenda items matching the query.

    Scans DynamoDB and scores in-memory. Fine for ~400 items.
    """
    items = query_all_agenda_items(limit=1000)

    scored = []
    for item in items:
        score = _score_item(item, query)
        if score >= min_score:
            result = dict(item)
            result["search_score"] = round(score, 3)
            scored.append(result)

    scored.sort(key=lambda x: x["search_score"], reverse=True)
    return scored[:top_k]


def get_stats() -> dict:
    """Get search stats."""
    items = query_all_agenda_items(limit=1000)
    return {
        "total_items": len(items),
        "search_method": "keyword_scan",
        "backend": "dynamodb",
    }
