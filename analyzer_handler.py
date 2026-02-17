"""Lambda handler for AI analysis (SQS-triggered).

Receives analysis jobs from SQS, runs Bedrock analysis on meeting agenda items,
and writes enriched items back to DynamoDB.
"""

import json
import os


def handler(event, context):
    """Handle SQS-triggered analysis jobs.

    Expected SQS message body:
    {
        "meeting_id": "abc-123",
        "action": "analyze_meeting"
    }
    """
    from spokane_public_brief.analyzer import analyze_document
    from spokane_public_brief.models.dynamodb import (
        get_agenda_items_for_meeting,
        put_agenda_item,
    )

    processed = 0

    for record in event.get("Records", []):
        body = json.loads(record["body"])
        meeting_id = body.get("meeting_id")

        if not meeting_id:
            print(f"Skipping record with no meeting_id: {body}")
            continue

        items = get_agenda_items_for_meeting(meeting_id)
        if not items:
            print(f"No items found for meeting {meeting_id}")
            continue

        # Build text from agenda items
        text = "\n\n".join(
            f"Item: {item.get('title', '')}\n{item.get('summary', '')}"
            for item in items
        )

        print(f"Analyzing meeting {meeting_id} ({len(items)} items)")
        result = analyze_document(text, doc_type="agenda")
        print(f"Analysis complete: {len(result.get('items', []))} items returned")

        # Update items with analysis results
        for analyzed in result.get("items", []):
            put_agenda_item({
                "meeting_id": meeting_id,
                **analyzed,
            })

        processed += 1

    return {
        "statusCode": 200,
        "body": json.dumps({"message": f"Analyzed {processed} meetings"}),
    }
