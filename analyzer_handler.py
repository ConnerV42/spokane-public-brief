"""Lambda handler for AI analysis (SQS-triggered).

Receives analysis jobs from SQS, runs Bedrock analysis on meeting agenda items,
and writes enriched items back to DynamoDB.
"""

import json
import logging
import os

logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


def handler(event, context):
    """Handle SQS-triggered analysis jobs.

    Expected SQS message body:
    {
        "meeting_id": "abc-123",
        "action": "analyze_meeting"
    }
    """
    from spokane_public_brief.analyzer import analyze_document, AnalyzerError
    from spokane_public_brief.models.dynamodb import (
        DynamoDBError,
        get_agenda_items_for_meeting,
        put_agenda_item,
    )

    processed = 0
    errors = []

    for record in event.get("Records", []):
        message_id = record.get("messageId", "unknown")
        try:
            body = json.loads(record["body"])
        except (json.JSONDecodeError, KeyError) as e:
            logger.error("Invalid SQS message %s: %s", message_id, e)
            errors.append({"message_id": message_id, "error": f"Invalid message: {e}"})
            continue

        meeting_id = body.get("meeting_id")
        if not meeting_id:
            logger.warning("Skipping SQS message %s: no meeting_id", message_id)
            errors.append({"message_id": message_id, "error": "Missing meeting_id"})
            continue

        try:
            items = get_agenda_items_for_meeting(meeting_id)
        except DynamoDBError as e:
            logger.error("Failed to fetch agenda items for meeting %s: %s", meeting_id, e)
            errors.append({"meeting_id": meeting_id, "error": f"DynamoDB read failed: {e}"})
            continue

        if not items:
            logger.info("No items found for meeting %s, skipping", meeting_id)
            continue

        # Build text from agenda items
        text = "\n\n".join(
            f"Item: {item.get('title', '')}\n{item.get('summary', '')}"
            for item in items
        )

        logger.info("Analyzing meeting %s (%d items)", meeting_id, len(items))

        try:
            result = analyze_document(text, doc_type="agenda")
        except AnalyzerError as e:
            logger.error("Analysis failed for meeting %s: %s", meeting_id, e)
            errors.append({"meeting_id": meeting_id, "error": f"Analysis failed: {e}"})
            continue

        if "error" in result:
            logger.warning("Analysis returned error for meeting %s: %s", meeting_id, result["error"])

        logger.info("Analysis complete for %s: %d items returned", meeting_id, len(result.get("items", [])))

        # Update items with analysis results
        for analyzed in result.get("items", []):
            try:
                put_agenda_item({
                    "meeting_id": meeting_id,
                    **analyzed,
                })
            except DynamoDBError as e:
                logger.error("Failed to store analyzed item for meeting %s: %s", meeting_id, e)
                errors.append({"meeting_id": meeting_id, "error": f"DynamoDB write failed: {e}"})

        processed += 1

    response = {
        "statusCode": 200,
        "body": json.dumps({
            "message": f"Analyzed {processed} meetings",
            "errors": len(errors),
        }),
    }

    if errors:
        logger.warning("Completed with %d errors: %s", len(errors), json.dumps(errors))

    return response
