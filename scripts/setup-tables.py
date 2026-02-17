#!/usr/bin/env python3
"""Create DynamoDB tables for local development."""

import boto3
from botocore.exceptions import ClientError

import os
DYNAMODB_ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT", "http://localhost:8001")

def get_dynamodb():
    return boto3.client(
        "dynamodb",
        endpoint_url=DYNAMODB_ENDPOINT,
        region_name="us-west-2",
        aws_access_key_id="local",
        aws_secret_access_key="local",
    )


def create_table(client, table_def):
    """Create a table, skip if already exists."""
    table_name = table_def["TableName"]
    print(f"Creating table: {table_name}")
    
    try:
        existing = client.describe_table(TableName=table_name)
        print(f"  Table already exists, skipping")
        return
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceNotFoundException":
            raise
    
    client.create_table(**table_def)
    print(f"  Created!")


def main():
    print("=== Creating DynamoDB Local Tables ===\n")
    client = get_dynamodb()
    
    # Meetings table with body-date-index GSI
    create_table(client, {
        "TableName": os.environ.get("MEETINGS_TABLE", "spokane-public-brief-meetings-dev"),
        "AttributeDefinitions": [
            {"AttributeName": "meeting_id", "AttributeType": "S"},
            {"AttributeName": "body_name", "AttributeType": "S"},
            {"AttributeName": "meeting_date", "AttributeType": "S"},
        ],
        "KeySchema": [
            {"AttributeName": "meeting_id", "KeyType": "HASH"},
        ],
        "GlobalSecondaryIndexes": [
            {
                "IndexName": "body-date-index",
                "KeySchema": [
                    {"AttributeName": "body_name", "KeyType": "HASH"},
                    {"AttributeName": "meeting_date", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        "BillingMode": "PAY_PER_REQUEST",
    })
    
    # Agenda items table with meeting-index GSI
    create_table(client, {
        "TableName": os.environ.get("AGENDA_TABLE", "spokane-public-brief-agenda-items-dev"),
        "AttributeDefinitions": [
            {"AttributeName": "item_id", "AttributeType": "S"},
            {"AttributeName": "meeting_id", "AttributeType": "S"},
        ],
        "KeySchema": [
            {"AttributeName": "item_id", "KeyType": "HASH"},
        ],
        "GlobalSecondaryIndexes": [
            {
                "IndexName": "meeting-index",
                "KeySchema": [
                    {"AttributeName": "meeting_id", "KeyType": "HASH"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        "BillingMode": "PAY_PER_REQUEST",
    })
    
    # Documents table
    create_table(client, {
        "TableName": os.environ.get("DOCUMENTS_TABLE", "spokane-public-brief-documents-dev"),
        "AttributeDefinitions": [
            {"AttributeName": "document_id", "AttributeType": "S"},
        ],
        "KeySchema": [
            {"AttributeName": "document_id", "KeyType": "HASH"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
    })
    
    print("\n=== Tables created ===")
    tables = client.list_tables()
    for t in tables["TableNames"]:
        print(f"  - {t}")


if __name__ == "__main__":
    main()
