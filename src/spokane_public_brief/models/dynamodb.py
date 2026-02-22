"""DynamoDB data access for Spokane Public Brief v2.

Replaces SQLAlchemy/PostgreSQL with boto3 DynamoDB.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Optional

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError, BotoCoreError

from spokane_public_brief.config import settings

logger = logging.getLogger(__name__)


class DynamoDBError(Exception):
    """Raised when a DynamoDB operation fails."""
    def __init__(self, operation: str, table: str, detail: str):
        self.operation = operation
        self.table = table
        self.detail = detail
        super().__init__(f"DynamoDB {operation} on {table} failed: {detail}")


def _get_table(table_name: str):
    """Get a DynamoDB table resource (supports DYNAMODB_ENDPOINT for local dev)."""
    return settings.get_dynamodb_table(table_name)


# --- Meetings ---

def put_meeting(meeting: dict) -> str:
    """Store a meeting. Returns meeting_id."""
    table_name = settings.meetings_table
    meeting_id = meeting.get("meeting_id") or str(uuid.uuid4())

    item = {
        "meeting_id": meeting_id,
        "_type": "meeting",
        "body_name": meeting.get("body_name", "City Council"),
        "meeting_date": meeting.get("meeting_date", ""),
        "title": meeting.get("title", ""),
        "location": meeting.get("location", ""),
        "url": meeting.get("url", ""),
        "source": meeting.get("source", "spokane_city"),
        "created_at": datetime.utcnow().isoformat(),
    }

    try:
        table = _get_table(table_name)
        table.put_item(Item=item)
        logger.info("Stored meeting %s in %s", meeting_id, table_name)
        return meeting_id
    except (ClientError, BotoCoreError) as e:
        logger.error("Failed to store meeting %s: %s", meeting_id, e)
        raise DynamoDBError("put_item", table_name, str(e)) from e


def get_meeting(meeting_id: str) -> Optional[dict]:
    """Get a meeting by ID."""
    table_name = settings.meetings_table
    try:
        table = _get_table(table_name)
        resp = table.get_item(Key={"meeting_id": meeting_id})
        return resp.get("Item")
    except (ClientError, BotoCoreError) as e:
        logger.error("Failed to get meeting %s: %s", meeting_id, e)
        raise DynamoDBError("get_item", table_name, str(e)) from e


def list_meetings(body_name: Optional[str] = None, limit: int = 50) -> list[dict]:
    """List meetings, optionally filtered by body."""
    table_name = settings.meetings_table
    try:
        table = _get_table(table_name)

        if body_name:
            resp = table.query(
                IndexName="body-date-index",
                KeyConditionExpression=Key("body_name").eq(body_name),
                ScanIndexForward=False,
                Limit=limit,
            )
        else:
            resp = table.query(
                IndexName="type-date-index",
                KeyConditionExpression=Key("_type").eq("meeting"),
                ScanIndexForward=False,
                Limit=limit,
            )

        return resp.get("Items", [])
    except (ClientError, BotoCoreError) as e:
        logger.error("Failed to list meetings (body=%s): %s", body_name, e)
        raise DynamoDBError("query/scan", table_name, str(e)) from e


# --- Agenda Items ---

def put_agenda_item(item: dict) -> str:
    """Store an agenda item. Returns item_id."""
    table_name = settings.agenda_table
    item_id = item.get("item_id") or str(uuid.uuid4())

    record = {
        "item_id": item_id,
        "_type": "agenda_item",
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

    try:
        table = _get_table(table_name)
        table.put_item(Item=record)
        logger.debug("Stored agenda item %s for meeting %s", item_id, record.get("meeting_id"))
        return item_id
    except (ClientError, BotoCoreError) as e:
        logger.error("Failed to store agenda item %s: %s", item_id, e)
        raise DynamoDBError("put_item", table_name, str(e)) from e


def get_agenda_items_for_meeting(meeting_id: str) -> list[dict]:
    """Get all agenda items for a meeting."""
    table_name = settings.agenda_table
    try:
        table = _get_table(table_name)
        resp = table.query(
            IndexName="meeting-index",
            KeyConditionExpression=Key("meeting_id").eq(meeting_id),
        )
        return resp.get("Items", [])
    except (ClientError, BotoCoreError) as e:
        logger.error("Failed to get agenda items for meeting %s: %s", meeting_id, e)
        raise DynamoDBError("query", table_name, str(e)) from e


def query_all_agenda_items(limit: int = 500) -> list[dict]:
    """Query all agenda items via type-date GSI. Returns newest first."""
    table_name = settings.agenda_table
    try:
        table = _get_table(table_name)
        items = []
        kwargs = {
            "IndexName": "type-date-index",
            "KeyConditionExpression": Key("_type").eq("agenda_item"),
            "ScanIndexForward": False,
            "Limit": limit,
        }
        resp = table.query(**kwargs)
        items.extend(resp.get("Items", []))

        while "LastEvaluatedKey" in resp and len(items) < limit:
            kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
            kwargs["Limit"] = limit - len(items)
            resp = table.query(**kwargs)
            items.extend(resp.get("Items", []))

        return items
    except (ClientError, BotoCoreError) as e:
        logger.error("Failed to query agenda items: %s", e)
        raise DynamoDBError("query", table_name, str(e)) from e


def query_agenda_items_by_topic(topic: str, limit: int = 200) -> list[dict]:
    """Query agenda items by topic via topic-date GSI. Returns newest first."""
    table_name = settings.agenda_table
    try:
        table = _get_table(table_name)
        resp = table.query(
            IndexName="topic-date-index",
            KeyConditionExpression=Key("topic").eq(topic),
            ScanIndexForward=False,
            Limit=limit,
        )
        return resp.get("Items", [])
    except (ClientError, BotoCoreError) as e:
        logger.error("Failed to query agenda items by topic %s: %s", topic, e)
        raise DynamoDBError("query", table_name, str(e)) from e


# Keep backward compat alias — but warn if called
def scan_all_agenda_items(limit: int = 500) -> list[dict]:
    """DEPRECATED: Use query_all_agenda_items instead."""
    logger.warning("scan_all_agenda_items is deprecated — use query_all_agenda_items")
    return query_all_agenda_items(limit=limit)


# --- Documents ---

def put_document(doc: dict) -> str:
    """Store a document reference."""
    table_name = settings.documents_table
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

    try:
        table = _get_table(table_name)
        table.put_item(Item=record)
        logger.info("Stored document %s", doc_id)
        return doc_id
    except (ClientError, BotoCoreError) as e:
        logger.error("Failed to store document %s: %s", doc_id, e)
        raise DynamoDBError("put_item", table_name, str(e)) from e
