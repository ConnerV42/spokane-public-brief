"""DynamoDB data access for Spokane Public Brief v2.

Replaces SQLAlchemy/PostgreSQL with boto3 DynamoDB.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Optional

import boto3
from boto3.dynamodb.conditions import Key

from spokane_public_brief.config import settings


def _get_table(table_name: str):
    """Get a DynamoDB table resource."""
    dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
    return dynamodb.Table(table_name)


# --- Meetings ---

def put_meeting(meeting: dict) -> str:
    """Store a meeting. Returns meeting_id."""
    table = _get_table(settings.meetings_table)
    meeting_id = meeting.get("meeting_id") or str(uuid.uuid4())

    item = {
        "meeting_id": meeting_id,
        "body_name": meeting.get("body_name", "City Council"),
        "meeting_date": meeting.get("meeting_date", ""),
        "title": meeting.get("title", ""),
        "location": meeting.get("location", ""),
        "url": meeting.get("url", ""),
        "source": meeting.get("source", "spokane_city"),
        "created_at": datetime.utcnow().isoformat(),
    }
    table.put_item(Item=item)
    return meeting_id


def get_meeting(meeting_id: str) -> Optional[dict]:
    """Get a meeting by ID."""
    table = _get_table(settings.meetings_table)
    resp = table.get_item(Key={"meeting_id": meeting_id})
    return resp.get("Item")


def list_meetings(body_name: Optional[str] = None, limit: int = 50) -> list[dict]:
    """List meetings, optionally filtered by body."""
    table = _get_table(settings.meetings_table)

    if body_name:
        resp = table.query(
            IndexName="body-date-index",
            KeyConditionExpression=Key("body_name").eq(body_name),
            ScanIndexForward=False,
            Limit=limit,
        )
    else:
        resp = table.scan(Limit=limit)

    return resp.get("Items", [])


# --- Agenda Items ---

def put_agenda_item(item: dict) -> str:
    """Store an agenda item. Returns item_id."""
    table = _get_table(settings.agenda_table)
    item_id = item.get("item_id") or str(uuid.uuid4())

    record = {
        "item_id": item_id,
        "meeting_id": item.get("meeting_id", ""),
        "title": item.get("title", ""),
        "topic": item.get("topic", "other"),
        "relevance": item.get("relevance", 1),
        "summary": item.get("summary", ""),
        "key_details": item.get("key_details", []),
        "why_it_matters": item.get("why_it_matters", ""),
        "status": item.get("status", ""),
        "decision": item.get("decision"),
        "economic_axis": item.get("economic_axis", 0),
        "social_axis": item.get("social_axis", 0),
        "meeting_date": item.get("meeting_date", ""),
        "created_at": datetime.utcnow().isoformat(),
    }
    # DynamoDB doesn't like empty strings in non-key attributes for some types
    record = {k: v for k, v in record.items() if v is not None}
    table.put_item(Item=record)
    return item_id


def get_agenda_items_for_meeting(meeting_id: str) -> list[dict]:
    """Get all agenda items for a meeting."""
    table = _get_table(settings.agenda_table)
    resp = table.query(
        IndexName="meeting-index",
        KeyConditionExpression=Key("meeting_id").eq(meeting_id),
    )
    return resp.get("Items", [])


def scan_all_agenda_items(limit: int = 500) -> list[dict]:
    """Scan all agenda items (for search). Use sparingly — full table scan."""
    table = _get_table(settings.agenda_table)
    items = []
    resp = table.scan(Limit=limit)
    items.extend(resp.get("Items", []))

    # Handle pagination
    while "LastEvaluatedKey" in resp and len(items) < limit:
        resp = table.scan(
            ExclusiveStartKey=resp["LastEvaluatedKey"],
            Limit=limit - len(items),
        )
        items.extend(resp.get("Items", []))

    return items


# --- Documents ---

def put_document(doc: dict) -> str:
    """Store a document reference."""
    table = _get_table(settings.documents_table)
    doc_id = doc.get("document_id") or str(uuid.uuid4())

    record = {
        "document_id": doc_id,
        "meeting_id": doc.get("meeting_id", ""),
        "title": doc.get("title", ""),
        "document_type": doc.get("document_type", ""),
        "url": doc.get("url", ""),
        "processed": doc.get("processed", False),
        "created_at": datetime.utcnow().isoformat(),
    }
    record = {k: v for k, v in record.items() if v is not None}
    table.put_item(Item=record)
    return doc_id
