"""Shared fixtures for Spokane Public Brief tests."""

import os
import pytest
import boto3
from moto import mock_aws


# Force local/test settings before any app imports
os.environ["STAGE"] = "test"
os.environ["AWS_DEFAULT_REGION"] = "us-west-2"
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SECURITY_TOKEN"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"
os.environ["MEETINGS_TABLE"] = "test-meetings"
os.environ["AGENDA_TABLE"] = "test-agenda-items"
os.environ["DOCUMENTS_TABLE"] = "test-documents"


@pytest.fixture
def aws_mock():
    """Mock all AWS services."""
    with mock_aws():
        yield


@pytest.fixture
def dynamodb_tables(aws_mock):
    """Create DynamoDB tables for testing."""
    dynamodb = boto3.client("dynamodb", region_name="us-west-2")

    # Meetings table
    dynamodb.create_table(
        TableName="test-meetings",
        KeySchema=[{"AttributeName": "meeting_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "meeting_id", "AttributeType": "S"},
            {"AttributeName": "body_name", "AttributeType": "S"},
            {"AttributeName": "meeting_date", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "body-date-index",
                "KeySchema": [
                    {"AttributeName": "body_name", "KeyType": "HASH"},
                    {"AttributeName": "meeting_date", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    # Agenda items table
    dynamodb.create_table(
        TableName="test-agenda-items",
        KeySchema=[{"AttributeName": "item_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "item_id", "AttributeType": "S"},
            {"AttributeName": "meeting_id", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "meeting-index",
                "KeySchema": [
                    {"AttributeName": "meeting_id", "KeyType": "HASH"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    # Documents table
    dynamodb.create_table(
        TableName="test-documents",
        KeySchema=[{"AttributeName": "document_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "document_id", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    yield dynamodb


@pytest.fixture
def sample_meeting():
    """A sample meeting dict."""
    return {
        "meeting_id": "mtg-001",
        "body_name": "City Council",
        "title": "Regular City Council Meeting",
        "meeting_date": "2026-02-20T18:00:00",
        "location": "Council Chambers",
        "url": "https://spokane.legistar.com/mtg-001",
        "source": "spokane_city",
    }


@pytest.fixture
def sample_agenda_item():
    """A sample agenda item dict."""
    return {
        "item_id": "item-001",
        "meeting_id": "mtg-001",
        "title": "Rezoning of North Monroe corridor",
        "topic": "zoning",
        "relevance": 4,
        "summary": "Proposed rezoning to mixed-use for 12 blocks along Monroe St.",
        "key_details": ["12 blocks affected", "$2.5M infrastructure cost"],
        "why_it_matters": "Could bring 200+ housing units to underserved area.",
        "status": "first_reading",
        "decision": "pending",
        "economic_axis": 2,
        "social_axis": 0,
        "meeting_date": "2026-02-20T18:00:00",
    }
