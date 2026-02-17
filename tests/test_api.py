"""Tests for the FastAPI application with mocked DynamoDB."""

import pytest
from fastapi.testclient import TestClient

from spokane_public_brief.models.dynamodb import put_meeting, put_agenda_item
from spokane_public_brief.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:
    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["version"] == "2.0.0"


class TestMeetingsEndpoint:
    def test_list_meetings_empty(self, dynamodb_tables, client):
        resp = client.get("/api/meetings")
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    def test_list_meetings_with_data(self, dynamodb_tables, client, sample_meeting):
        put_meeting(sample_meeting)
        resp = client.get("/api/meetings")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["meetings"][0]["meeting_id"] == "mtg-001"

    def test_list_meetings_filter_by_body(self, dynamodb_tables, client, sample_meeting):
        put_meeting(sample_meeting)
        put_meeting({**sample_meeting, "meeting_id": "mtg-002", "body_name": "Plan Commission"})

        resp = client.get("/api/meetings?body=City Council")
        data = resp.json()
        assert data["count"] == 1
        assert data["meetings"][0]["body_name"] == "City Council"

    def test_meeting_detail(self, dynamodb_tables, client, sample_meeting, sample_agenda_item):
        put_meeting(sample_meeting)
        put_agenda_item(sample_agenda_item)

        resp = client.get("/api/meetings/mtg-001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["meeting"]["meeting_id"] == "mtg-001"
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Rezoning of North Monroe corridor"

    def test_meeting_detail_not_found(self, dynamodb_tables, client):
        resp = client.get("/api/meetings/nonexistent")
        assert resp.status_code == 404


class TestItemsEndpoint:
    def test_list_items_empty(self, dynamodb_tables, client):
        resp = client.get("/api/items")
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    def test_list_items_with_data(self, dynamodb_tables, client, sample_agenda_item):
        put_agenda_item(sample_agenda_item)
        resp = client.get("/api/items")
        data = resp.json()
        assert data["count"] == 1

    def test_items_filter_by_topic(self, dynamodb_tables, client, sample_agenda_item):
        put_agenda_item(sample_agenda_item)
        put_agenda_item({**sample_agenda_item, "item_id": "item-002", "topic": "budget", "relevance": 2})

        resp = client.get("/api/items?topic=zoning")
        data = resp.json()
        assert data["count"] == 1
        assert data["items"][0]["topic"] == "zoning"

    def test_items_filter_by_relevance(self, dynamodb_tables, client, sample_agenda_item):
        put_agenda_item(sample_agenda_item)  # relevance=4
        put_agenda_item({**sample_agenda_item, "item_id": "item-002", "relevance": 1})

        resp = client.get("/api/items?min_relevance=3")
        data = resp.json()
        assert data["count"] == 1


class TestSearchEndpoint:
    def test_search_finds_match(self, dynamodb_tables, client, sample_agenda_item):
        put_agenda_item(sample_agenda_item)
        resp = client.get("/api/search?q=rezoning Monroe")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1
        assert data["results"][0]["title"] == "Rezoning of North Monroe corridor"

    def test_search_no_match(self, dynamodb_tables, client, sample_agenda_item):
        put_agenda_item(sample_agenda_item)
        resp = client.get("/api/search?q=xyznonexistent")
        data = resp.json()
        assert data["count"] == 0

    def test_search_requires_query(self, client):
        resp = client.get("/api/search")
        assert resp.status_code == 422  # FastAPI validation


class TestStatsEndpoint:
    def test_stats_empty(self, dynamodb_tables, client):
        resp = client.get("/api/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["meetings"] == 0
        assert data["agenda_items"] == 0

    def test_stats_with_data(self, dynamodb_tables, client, sample_meeting, sample_agenda_item):
        put_meeting(sample_meeting)
        put_agenda_item(sample_agenda_item)
        resp = client.get("/api/stats")
        data = resp.json()
        assert data["meetings"] == 1
        assert data["agenda_items"] == 1
        assert data["high_relevance"] == 1
        assert "zoning" in data["topics"]
