"""Lambda handler for Legistar ingestion (SQS-triggered or scheduled).

Fetches meetings from Legistar, stores in DynamoDB, optionally analyzes with Bedrock.
"""

import json
import os

from spokane_public_brief.ingestors.legistar import LegistarClient, fetch_upcoming_meetings
from spokane_public_brief.models.dynamodb import (
    put_meeting,
    put_agenda_item,
    get_agenda_items_for_meeting,
)


def handler(event, context):
    """Handle SQS or scheduled ingestion triggers."""
    if "Records" in event:
        # SQS trigger — process specific items
        for record in event["Records"]:
            body = json.loads(record["body"])
            action = body.get("action", "ingest_meetings")
            if action == "ingest_meetings":
                _ingest_meetings()
            elif action == "analyze_meeting":
                meeting_id = body.get("meeting_id")
                if meeting_id:
                    _analyze_meeting(meeting_id)
    else:
        # Scheduled trigger — full ingest
        _ingest_meetings()

    return {"statusCode": 200, "body": json.dumps({"message": "Ingest complete"})}


def _ingest_meetings():
    """Fetch and store upcoming meetings from Legistar."""
    meetings = fetch_upcoming_meetings()
    print(f"Fetched {len(meetings)} upcoming meetings from Legistar")

    client = LegistarClient("spokane")
    stored = 0

    for meeting in meetings:
        meeting_id = put_meeting(meeting)

        # Fetch agenda items for this meeting
        event_id = int(meeting["meeting_id"])
        try:
            event_items = client.get_event_items(event_id)
            for item in event_items:
                title = item.get("EventItemTitle", "")
                if not title or title.strip() == "":
                    continue
                put_agenda_item({
                    "meeting_id": meeting_id,
                    "title": title,
                    "topic": "other",
                    "relevance": 1,
                    "summary": "",
                    "meeting_date": meeting.get("meeting_date", ""),
                })
            stored += 1
        except Exception as e:
            print(f"Error fetching items for event {event_id}: {e}")

    print(f"Stored {stored} meetings with agenda items")


def _analyze_meeting(meeting_id: str):
    """Analyze a meeting's agenda items with Bedrock."""
    from spokane_public_brief.analyzer import analyze_document

    items = get_agenda_items_for_meeting(meeting_id)
    if not items:
        print(f"No items found for meeting {meeting_id}")
        return

    # Build text from items
    text = "\n\n".join(
        f"Item: {item.get('title', '')}\n{item.get('summary', '')}"
        for item in items
    )

    result = analyze_document(text, doc_type="agenda")
    print(f"Analyzed meeting {meeting_id}: {len(result.get('items', []))} items")

    # Update items with analysis
    for analyzed in result.get("items", []):
        put_agenda_item({
            "meeting_id": meeting_id,
            **analyzed,
        })
