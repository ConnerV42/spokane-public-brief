"""AI-powered document analyzer using AWS Bedrock (Claude).

Replaces direct Anthropic API with Bedrock Runtime.
"""

import json
import os
from typing import Any

import boto3

from spokane_public_brief.config import settings

# Topics for classification
TOPICS = [
    "housing", "zoning", "taxes", "budget", "transportation",
    "parks", "environment", "public_safety", "infrastructure",
    "development", "permits", "other",
]


def _get_bedrock_client():
    """Get Bedrock Runtime client."""
    return boto3.client("bedrock-runtime", region_name=settings.aws_region)


def analyze_document(text: str, doc_type: str = "agenda") -> dict[str, Any]:
    """Analyze a document using Claude via Bedrock.

    Uses the Bedrock Messages API (Claude 3.5 Sonnet on Bedrock).
    """
    client = _get_bedrock_client()

    prompt = f"""You are analyzing a Spokane City Council {doc_type} for citizens who want to stay informed.

Extract DETAILED, SPECIFIC information for each significant agenda item.

For EACH item, provide:
1. title: Clear name
2. topic: One of {TOPICS}
3. relevance: 1-5 (5 = highest public interest)
4. summary: 2-3 sentences
5. key_details: Bullet points of specific facts (dollar amounts, locations, timelines)
6. why_it_matters: One sentence on citizen impact
7. status: first_reading, final_reading, hearing, consent, action, or informational
8. decision: approved/denied/deferred/pending (if applicable)
9. economic_axis: -5 (left) to +5 (right), 0 = neutral
10. social_axis: -5 (libertarian) to +5 (authoritarian), 0 = neutral

Return JSON:
{{
  "summary": "overview",
  "items": [{{ ... }}],
  "notable_items": ["..."]
}}

Document text:
{text[:20000]}"""

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4000,
        "messages": [{"role": "user", "content": prompt}],
    })

    # Use Claude 3.5 Sonnet on Bedrock
    model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    response = client.invoke_model(
        modelId=model_id,
        body=body,
        contentType="application/json",
        accept="application/json",
    )

    result_body = json.loads(response["body"].read())
    response_text = result_body["content"][0]["text"]

    # Parse JSON from response
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(response_text[start:end])
        return {"error": "Failed to parse response", "raw": response_text}
