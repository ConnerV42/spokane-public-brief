"""Lambda handler for Legistar ingestion (EventBridge-scheduled or SQS-triggered).

Fetches meetings from Legistar, stores in DynamoDB, queues analysis jobs to SQS.
Analysis is handled by the separate analyzer Lambda.
"""

import json
import logging
import os

import boto3
from botocore.exceptions import ClientError, BotoCoreError

from spokane_public_brief.ingestors.legistar import LegistarClient, fetch_upcoming_meetings
from spokane_public_brief.models.dynamodb import (
    DynamoDBError,
    put_meeting,
    put_agenda_item,
    get_agenda_items_for_meeting,
)

logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


def _get_sqs_client():
    """Get SQS client."""
    return boto3.client("sqs", region_name=os.environ.get("AWS_REGION", "us-west-2"))


def _queue_analysis(meeting_id: str):
    """Queue a meeting for analysis by the analyzer Lambda."""
    queue_url = os.environ.get("ANALYSIS_QUEUE_URL")
    if not queue_url:
        logger.warning("ANALYSIS_QUEUE_URL not set, skipping analysis for %s", meeting_id)
        return

    try:
        sqs = _get_sqs_client()
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps({
                "action": "analyze_meeting",
                "meeting_id": meeting_id,
            }),
        )
        logger.info("Queued analysis job for meeting %s", meeting_id)
    except (ClientError, BotoCoreError) as e:
        logger.error("Failed to queue analysis for meeting %s: %s", meeting_id, e)
        # Don't raise — ingestion succeeded, analysis can be retried


def handler(event, context):
    """Handle scheduled or SQS ingestion triggers."""
    if "Records" in event:
        # SQS trigger — process specific items
        for record in event["Records"]:
            try:
                body = json.loads(record["body"])
            except (json.JSONDecodeError, KeyError) as e:
                logger.error("Invalid SQS record: %s", e)
                continue
            action = body.get("action", "ingest_meetings")
            if action == "ingest_meetings":
                _ingest_meetings()
    else:
        # Scheduled trigger (EventBridge) — full ingest
        _ingest_meetings()

    return {"statusCode": 200, "body": json.dumps({"message": "Ingest complete"})}


def _ingest_meetings():
    """Fetch and store upcoming meetings from Legistar, then queue for analysis."""
    try:
        meetings = fetch_upcoming_meetings()
    except Exception as e:
        logger.error("Failed to fetch meetings from Legistar: %s", e)
        return

    logger.info("Fetched %d upcoming meetings from Legistar", len(meetings))

    client = LegistarClient("spokane")
    stored = 0
    errors = 0

    for meeting in meetings:
        try:
            meeting_id = put_meeting(meeting)
        except DynamoDBError as e:
            logger.error("Failed to store meeting: %s", e)
            errors += 1
            continue

        # Fetch agenda items for this meeting
        event_id_str = meeting.get("meeting_id", "")
        try:
            event_id = int(event_id_str)
        except (ValueError, TypeError):
            logger.warning("Invalid event_id '%s' for meeting %s, skipping items", event_id_str, meeting_id)
            stored += 1
            _queue_analysis(meeting_id)
            continue

        try:
            event_items = client.get_event_items(event_id)
        except Exception as e:
            logger.error("Failed to fetch items for event %d: %s", event_id, e)
            errors += 1
            # Still count as stored since the meeting itself was saved
            stored += 1
            _queue_analysis(meeting_id)
            continue

        for item in event_items:
            title = item.get("EventItemTitle", "")
            if not title or title.strip() == "":
                continue
            try:
                put_agenda_item({
                    "meeting_id": meeting_id,
                    "title": title,
                    "topic": "other",
                    "relevance": 1,
                    "summary": "",
                    "meeting_date": meeting.get("meeting_date", ""),
                })
            except DynamoDBError as e:
                logger.error("Failed to store agenda item '%s': %s", title[:50], e)
                errors += 1

        stored += 1
        _queue_analysis(meeting_id)

    logger.info("Stored %d meetings (%d errors), queued for analysis", stored, errors)
