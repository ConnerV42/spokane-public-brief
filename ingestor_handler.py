"""Lambda handler for Legistar ingestion (EventBridge-scheduled or SQS-triggered).

Fetches meetings from Legistar, stores in DynamoDB, queues analysis jobs to SQS.
Analysis is handled by the separate analyzer Lambda.
"""

import json
import os

import boto3

from spokane_public_brief.ingestors.legistar import LegistarClient, fetch_upcoming_meetings
from spokane_public_brief.models.dynamodb import (
    put_meeting,
    put_agenda_item,
    get_agenda_items_for_meeting,
)


def _get_sqs_client():
    """Get SQS client."""
    return boto3.client("sqs", region_name=os.environ.get("AWS_REGION", "us-west-2"))


def _queue_analysis(meeting_id: str):
    """Queue a meeting for analysis by the analyzer Lambda."""
    queue_url = os.environ.get("ANALYSIS_QUEUE_URL")
    if not queue_url:
        print(f"ANALYSIS_QUEUE_URL not set, skipping analysis for {meeting_id}")
        return

    sqs = _get_sqs_client()
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps({
            "action": "analyze_meeting",
            "meeting_id": meeting_id,
        }),
    )
    print(f"Queued analysis job for meeting {meeting_id}")


def handler(event, context):
    """Handle scheduled or SQS ingestion triggers."""
    if "Records" in event:
        # SQS trigger — process specific items
        for record in event["Records"]:
            body = json.loads(record["body"])
            action = body.get("action", "ingest_meetings")
            if action == "ingest_meetings":
                _ingest_meetings()
    else:
        # Scheduled trigger (EventBridge) — full ingest
        _ingest_meetings()

    return {"statusCode": 200, "body": json.dumps({"message": "Ingest complete"})}


def _ingest_meetings():
    """Fetch and store upcoming meetings from Legistar, then queue for analysis."""
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

            # Queue this meeting for AI analysis
            _queue_analysis(meeting_id)

        except Exception as e:
            print(f"Error fetching items for event {event_id}: {e}")

    print(f"Stored {stored} meetings with agenda items, queued for analysis")
