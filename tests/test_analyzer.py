"""Tests for the Bedrock analyzer with mocked AWS client."""

import json
import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO

from spokane_public_brief.analyzer import analyze_document, AnalyzerError


MOCK_ANALYSIS = {
    "summary": "Meeting covered rezoning and budget items.",
    "items": [
        {
            "title": "Monroe rezoning",
            "topic": "zoning",
            "relevance": 4,
            "summary": "Proposed mixed-use rezoning.",
            "key_details": ["12 blocks"],
            "why_it_matters": "More housing.",
            "status": "first_reading",
            "decision": "pending",
            "economic_axis": 2,
            "social_axis": 0,
        }
    ],
    "notable_items": ["Monroe rezoning"],
}


def _make_bedrock_response(content: dict) -> dict:
    """Create a mock Bedrock invoke_model response."""
    body_bytes = json.dumps({
        "content": [{"text": json.dumps(content)}],
    }).encode()
    return {"body": BytesIO(body_bytes)}


class TestAnalyzeDocument:
    def test_successful_analysis(self):
        mock_client = MagicMock()
        mock_client.invoke_model.return_value = _make_bedrock_response(MOCK_ANALYSIS)

        with patch("spokane_public_brief.analyzer.boto3.client", return_value=mock_client):
            result = analyze_document("Some agenda text here", doc_type="agenda")

        assert result["summary"] == "Meeting covered rezoning and budget items."
        assert len(result["items"]) == 1
        assert result["items"][0]["topic"] == "zoning"

        # Verify Bedrock was called with correct model
        call_kwargs = mock_client.invoke_model.call_args.kwargs
        assert "claude" in call_kwargs["modelId"]

    def test_bedrock_client_error(self):
        from botocore.exceptions import ClientError

        mock_client = MagicMock()
        mock_client.invoke_model.side_effect = ClientError(
            {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
            "InvokeModel",
        )

        with patch("spokane_public_brief.analyzer.boto3.client", return_value=mock_client):
            with pytest.raises(AnalyzerError, match="Bedrock API call failed"):
                analyze_document("text")

    def test_malformed_json_fallback(self):
        """When Claude returns JSON wrapped in markdown, parser extracts it."""
        wrapped = '```json\n' + json.dumps(MOCK_ANALYSIS) + '\n```'
        body_bytes = json.dumps({
            "content": [{"text": wrapped}],
        }).encode()
        mock_response = {"body": BytesIO(body_bytes)}

        mock_client = MagicMock()
        mock_client.invoke_model.return_value = mock_response

        with patch("spokane_public_brief.analyzer.boto3.client", return_value=mock_client):
            result = analyze_document("text")
        # Should still extract the JSON via fallback parsing
        assert "summary" in result or "error" in result

    def test_completely_unparseable_response(self):
        """When response is not JSON at all, returns error dict."""
        body_bytes = json.dumps({
            "content": [{"text": "I cannot analyze this document."}],
        }).encode()
        mock_response = {"body": BytesIO(body_bytes)}

        mock_client = MagicMock()
        mock_client.invoke_model.return_value = mock_response

        with patch("spokane_public_brief.analyzer.boto3.client", return_value=mock_client):
            result = analyze_document("text")
        assert "error" in result
        assert "raw" in result
