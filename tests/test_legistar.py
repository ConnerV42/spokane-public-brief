"""Tests for the Legistar API client with mocked HTTP."""

import pytest
import httpx
from unittest.mock import patch, MagicMock

from spokane_public_brief.ingestors.legistar import (
    LegistarClient,
    LegistarAPIError,
    fetch_upcoming_meetings,
)


SAMPLE_EVENT = {
    "EventId": 42,
    "EventBodyName": "City Council",
    "EventDate": "2026-02-20T18:00:00",
    "EventLocation": "Council Chambers",
    "EventInSiteURL": "https://spokane.legistar.com/42",
}

SAMPLE_ITEM = {
    "EventItemId": 100,
    "EventItemTitle": "Rezoning proposal",
    "EventItemMover": "Council Member Smith",
}


class TestLegistarClient:
    def test_get_events_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [SAMPLE_EVENT]

        with patch("spokane_public_brief.ingestors.legistar.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            client = LegistarClient("spokane")
            events = client.get_events()
            assert len(events) == 1
            assert events[0]["EventId"] == 42

    def test_get_event_items_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [SAMPLE_ITEM]

        with patch("spokane_public_brief.ingestors.legistar.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            client = LegistarClient("spokane")
            items = client.get_event_items(42)
            assert len(items) == 1
            assert items[0]["EventItemTitle"] == "Rezoning proposal"

    def test_4xx_raises_legistar_error(self):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not found"

        with patch("spokane_public_brief.ingestors.legistar.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            client = LegistarClient("spokane")
            with pytest.raises(LegistarAPIError) as exc_info:
                client.get_events()
            assert exc_info.value.status_code == 404

    def test_5xx_retries_then_raises(self):
        """5xx should trigger retries (tenacity), eventually raise."""
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.text = "Service Unavailable"

        with patch("spokane_public_brief.ingestors.legistar.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            client = LegistarClient("spokane")
            # tenacity retries 3 times then reraises _RetryableHTTPError
            with pytest.raises(Exception):
                client.get_events()
            # Should have been called 3 times (initial + 2 retries)
            assert mock_client.get.call_count == 3


class TestFetchUpcomingMeetings:
    def test_formats_meetings(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [SAMPLE_EVENT]

        with patch("spokane_public_brief.ingestors.legistar.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            meetings = fetch_upcoming_meetings()
            assert len(meetings) == 1
            m = meetings[0]
            assert m["meeting_id"] == "42"
            assert m["body_name"] == "City Council"
            assert m["source"] == "spokane_city"
