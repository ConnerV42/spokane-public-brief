"""Legistar API ingestor for Spokane City Council.

Ported from v1 — async httpx replaced with sync httpx (Lambda-friendly).
Retry logic: 3 attempts with exponential backoff (1s, 2s, 4s) on transient errors.
"""

import logging
import httpx
from datetime import datetime
from typing import Any, Optional

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from spokane_public_brief.config import settings

logger = logging.getLogger(__name__)

# Retry on connection errors, timeouts, and 5xx responses
_RETRYABLE_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.ConnectTimeout,
    httpx.PoolTimeout,
)


class LegistarAPIError(Exception):
    """Raised when a Legistar API call fails after retries."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class _RetryableHTTPError(Exception):
    """Wrapper for 5xx responses that should be retried."""
    pass


def _check_response(response: httpx.Response) -> None:
    """Raise retryable error on 5xx, LegistarAPIError on 4xx."""
    if 500 <= response.status_code < 600:
        raise _RetryableHTTPError(
            f"Legistar API returned {response.status_code}: {response.text[:200]}"
        )
    if response.status_code >= 400:
        raise LegistarAPIError(
            f"Legistar API error: {response.status_code} - {response.text[:200]}",
            status_code=response.status_code,
        )


_retry_decorator = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    retry=retry_if_exception_type((*_RETRYABLE_EXCEPTIONS, _RetryableHTTPError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)


class LegistarClient:
    """Client for the Legistar Web API.

    Base URL: https://webapi.legistar.com/v1/{client}
    Spokane: https://webapi.legistar.com/v1/spokane
    """

    def __init__(self, client_name: str = "spokane"):
        self.client_name = client_name
        self.base_url = f"https://webapi.legistar.com/v1/{client_name}"

    @_retry_decorator
    def get_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[dict[str, Any]]:
        """Get events (meetings) from Legistar."""
        url = f"{self.base_url}/events"
        params = {}

        if start_date:
            params["$filter"] = f"EventDate ge datetime'{start_date.isoformat()}'"

        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, params=params)
            _check_response(response)
            return response.json()

    @_retry_decorator
    def get_event_items(self, event_id: int) -> list[dict[str, Any]]:
        """Get agenda items for a specific event."""
        url = f"{self.base_url}/events/{event_id}/eventitems"
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url)
            _check_response(response)
            return response.json()

    @_retry_decorator
    def get_bodies(self) -> list[dict[str, Any]]:
        """Get all legislative bodies."""
        url = f"{self.base_url}/bodies"
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url)
            _check_response(response)
            return response.json()


def fetch_upcoming_meetings() -> list[dict]:
    """Fetch upcoming meetings, formatted for DynamoDB storage."""
    client = LegistarClient("spokane")
    events = client.get_events(start_date=datetime.now())

    meetings = []
    for event in events:
        meetings.append({
            "source": "spokane_city",
            "meeting_id": str(event.get("EventId", "")),
            "body_name": event.get("EventBodyName", "City Council"),
            "title": event.get("EventBodyName", "City Council Meeting"),
            "meeting_date": event.get("EventDate", ""),
            "location": event.get("EventLocation", ""),
            "url": event.get("EventInSiteURL", ""),
        })

    return meetings
