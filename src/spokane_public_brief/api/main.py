"""FastAPI application for Spokane Public Brief v2 (serverless).

All data from DynamoDB. No file-based caches, no local state.
"""

import logging

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from spokane_public_brief.config import settings
from spokane_public_brief.models.dynamodb import (
    DynamoDBError,
    list_meetings,
    get_meeting,
    get_agenda_items_for_meeting,
    scan_all_agenda_items,
)
from spokane_public_brief import search as item_search

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Spokane Public Brief",
    description="AI-powered local government meeting scanner for Spokane",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- API Routes ---

@app.get("/api/health")
def health():
    """Health check."""
    return {
        "status": "healthy",
        "stage": settings.stage,
        "version": "2.0.0",
    }


@app.get("/api/meetings")
def api_meetings(body: str = Query(default=None), limit: int = Query(default=50, le=200)):
    """List meetings, optionally filtered by body name."""
    try:
        meetings = list_meetings(body_name=body, limit=limit)
    except DynamoDBError as e:
        logger.error("Failed to list meetings: %s", e)
        raise HTTPException(status_code=502, detail="Failed to retrieve meetings from database")
    return {
        "count": len(meetings),
        "meetings": meetings,
    }


@app.get("/api/meetings/{meeting_id}")
def api_meeting_detail(meeting_id: str):
    """Get a meeting with its agenda items."""
    try:
        meeting = get_meeting(meeting_id)
    except DynamoDBError as e:
        logger.error("Failed to get meeting %s: %s", meeting_id, e)
        raise HTTPException(status_code=502, detail="Failed to retrieve meeting from database")

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    try:
        items = get_agenda_items_for_meeting(meeting_id)
    except DynamoDBError as e:
        logger.error("Failed to get agenda items for %s: %s", meeting_id, e)
        raise HTTPException(status_code=502, detail="Failed to retrieve agenda items from database")

    return {
        "meeting": meeting,
        "items": items,
    }


@app.get("/api/items")
def api_items(
    topic: str = Query(default=None),
    min_relevance: int = Query(default=1, ge=1, le=5),
    limit: int = Query(default=50, le=200),
):
    """List agenda items with optional filters."""
    try:
        items = scan_all_agenda_items(limit=500)
    except DynamoDBError as e:
        logger.error("Failed to scan agenda items: %s", e)
        raise HTTPException(status_code=502, detail="Failed to retrieve items from database")

    # Filter
    if topic:
        items = [i for i in items if i.get("topic") == topic]
    if min_relevance > 1:
        items = [i for i in items if int(i.get("relevance", 1)) >= min_relevance]

    # Sort by relevance descending
    items.sort(key=lambda x: int(x.get("relevance", 1)), reverse=True)

    return {
        "count": len(items[:limit]),
        "items": items[:limit],
    }


@app.get("/api/search")
def api_search(q: str = Query(...), limit: int = Query(default=10, le=50)):
    """Search agenda items."""
    if not q:
        return {"error": "Query required", "results": []}

    try:
        results = item_search.search(q, top_k=limit, min_score=0.1)
        stats = item_search.get_stats()
    except DynamoDBError as e:
        logger.error("Search failed (DynamoDB): %s", e)
        raise HTTPException(status_code=502, detail="Search backend unavailable")
    except Exception as e:
        logger.error("Search failed: %s", e)
        raise HTTPException(status_code=500, detail="Search failed")

    return {
        "query": q,
        "count": len(results),
        "total_indexed": stats["total_items"],
        "results": results,
    }


@app.get("/api/stats")
def api_stats():
    """Dashboard stats."""
    try:
        items = scan_all_agenda_items(limit=1000)
        meetings = list_meetings(limit=500)
    except DynamoDBError as e:
        logger.error("Failed to get stats: %s", e)
        raise HTTPException(status_code=502, detail="Failed to retrieve stats from database")

    high_relevance = [i for i in items if int(i.get("relevance", 1)) >= 4]
    topics = set(i.get("topic") for i in items if i.get("topic"))

    return {
        "meetings": len(meetings),
        "agenda_items": len(items),
        "high_relevance": len(high_relevance),
        "topics": sorted(topics),
    }
