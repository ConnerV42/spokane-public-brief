"""Legistar API ingestor for Spokane City Council.

Ported from v1 — async httpx replaced with sync httpx (Lambda-friendly).
"""

import httpx
from datetime import datetime
from typing import Any, Optional

from spokane_public_brief.config import settings


class LegistarClient:
    """Client for the Legistar Web API.

    Base URL: https://webapi.legistar.com/v1/{client}
    Spokane: https://webapi.legistar.com/v1/spokane
    """

    def __init__(self, client_name: str = "spokane"):
        self.client_name = client_name
        self.base_url = f"https://webapi.legistar.com/v1/{client_name}"

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
            response.raise_for_status()
            return response.json()

    def get_event_items(self, event_id: int) -> list[dict[str, Any]]:
        """Get agenda items for a specific event."""
        url = f"{self.base_url}/events/{event_id}/eventitems"
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.json()

    def get_bodies(self) -> list[dict[str, Any]]:
        """Get all legislative bodies."""
        url = f"{self.base_url}/bodies"
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url)
            response.raise_for_status()
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
