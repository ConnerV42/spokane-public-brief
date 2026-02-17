"""FastAPI application for Spokane Public Brief v2 (serverless).

All data from DynamoDB. No file-based caches, no local state.
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from spokane_public_brief.config import settings
from spokane_public_brief.models.dynamodb import (
    list_meetings,
    get_meeting,
    get_agenda_items_for_meeting,
    scan_all_agenda_items,
)
from spokane_public_brief import search as item_search

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
    meetings = list_meetings(body_name=body, limit=limit)
    return {
        "count": len(meetings),
        "meetings": meetings,
    }


@app.get("/api/meetings/{meeting_id}")
def api_meeting_detail(meeting_id: str):
    """Get a meeting with its agenda items."""
    meeting = get_meeting(meeting_id)
    if not meeting:
        return {"error": "Meeting not found"}

    items = get_agenda_items_for_meeting(meeting_id)
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
    items = scan_all_agenda_items(limit=500)

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

    results = item_search.search(q, top_k=limit, min_score=0.1)
    stats = item_search.get_stats()

    return {
        "query": q,
        "count": len(results),
        "total_indexed": stats["total_items"],
        "results": results,
    }


@app.get("/api/stats")
def api_stats():
    """Dashboard stats."""
    items = scan_all_agenda_items(limit=1000)
    meetings = list_meetings(limit=500)

    high_relevance = [i for i in items if int(i.get("relevance", 1)) >= 4]
    topics = set(i.get("topic") for i in items if i.get("topic"))

    return {
        "meetings": len(meetings),
        "agenda_items": len(items),
        "high_relevance": len(high_relevance),
        "topics": sorted(topics),
    }
