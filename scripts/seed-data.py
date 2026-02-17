#!/usr/bin/env python3
"""
Seed DynamoDB Local with data for Spokane Public Brief development.

First tries Legistar API, falls back to sample data if API unavailable.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Any
from urllib.request import urlopen
from urllib.parse import quote
from urllib.error import URLError, HTTPError

import boto3
from botocore.exceptions import ClientError

# Configuration
DYNAMODB_ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT", "http://localhost:8001")
LEGISTAR_BASE_URL = "https://webapi.legistar.com/v1/spokane"
MEETINGS_TABLE = os.environ.get("MEETINGS_TABLE", "spokane-public-brief-meetings-dev")
AGENDA_TABLE = os.environ.get("AGENDA_TABLE", "spokane-public-brief-agenda-items-dev")
DOCUMENTS_TABLE = os.environ.get("DOCUMENTS_TABLE", "spokane-public-brief-documents-dev")

# Colors for output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"


def get_dynamodb():
    """Get DynamoDB resource with local endpoint override."""
    return boto3.resource(
        "dynamodb",
        endpoint_url=DYNAMODB_ENDPOINT,
        region_name="us-west-2",
        aws_access_key_id="local",
        aws_secret_access_key="local",
    )


def fetch_legistar_events(days_back: int = 60, days_forward: int = 30) -> list[dict]:
    """Fetch recent and upcoming events from Legistar API."""
    start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=days_forward)).strftime("%Y-%m-%d")
    
    filter_str = f"EventDate ge datetime'{start_date}' and EventDate le datetime'{end_date}'"
    url = f"{LEGISTAR_BASE_URL}/events?$filter={quote(filter_str)}"
    
    print(f"{YELLOW}Fetching events from Legistar API...{RESET}")
    print(f"  URL: {url}")
    
    try:
        with urlopen(url, timeout=30) as response:
            events = json.loads(response.read().decode())
            print(f"{GREEN}  Fetched {len(events)} events{RESET}")
            return events
    except (URLError, HTTPError) as e:
        print(f"{YELLOW}  Legistar API unavailable: {e}{RESET}")
        print(f"{YELLOW}  Using sample data instead{RESET}")
        return []


def generate_sample_events() -> list[dict]:
    """Generate sample events for local development."""
    print(f"{YELLOW}Generating sample meeting data...{RESET}")
    
    bodies = [
        "City Council",
        "Plan Commission",
        "Parks Board",
        "Civil Service Commission",
        "Spokane Regional Transportation Council",
        "Urban Development Committee",
    ]
    
    locations = [
        "Council Chambers, City Hall",
        "Lower Level Conference Room, City Hall", 
        "Spokane Municipal Court Building",
        "Spokane Arena",
    ]
    
    events = []
    base_date = datetime.now() - timedelta(days=30)
    
    for i in range(25):
        event_date = base_date + timedelta(days=i * 3)
        body = bodies[i % len(bodies)]
        
        event = {
            "EventId": 10000 + i,
            "EventGuid": f"sample-guid-{i:04d}",
            "EventBodyName": body,
            "EventDate": event_date.strftime("%Y-%m-%dT00:00:00"),
            "EventTime": "5:30 PM" if "Council" in body else "3:00 PM",
            "EventLocation": locations[i % len(locations)],
            "EventAgendaStatusName": "Final" if event_date < datetime.now() else "Draft",
            "EventMinutesStatusName": "Final" if event_date < datetime.now() - timedelta(days=7) else "",
            "EventAgendaFile": f"https://spokane.legistar.com/agenda{10000+i}.pdf" if event_date < datetime.now() + timedelta(days=7) else "",
            "EventMinutesFile": f"https://spokane.legistar.com/minutes{10000+i}.pdf" if event_date < datetime.now() - timedelta(days=7) else "",
            "EventLastModifiedUtc": datetime.now().isoformat(),
        }
        events.append(event)
    
    print(f"{GREEN}  Generated {len(events)} sample events{RESET}")
    return events


def generate_sample_items_for_meeting(event_id: int, body_name: str) -> list[dict]:
    """Generate sample agenda items for a meeting."""
    
    council_items = [
        ("Consent Agenda", "Approval of routine items including minutes, claims, and contracts"),
        ("Special Budget Appropriation - Public Safety", "Request for emergency funding for police department equipment"),
        ("Resolution - Climate Action Plan Update", "Review and adoption of updated climate action initiatives"),
        ("First Reading - Zoning Amendment", "Proposed changes to downtown mixed-use zoning regulations"),
        ("Public Comment Period", "Opportunity for citizens to address the council"),
        ("Mayor's Report", "Update on city initiatives and community events"),
        ("Council Member Reports", "Updates from individual council members"),
    ]
    
    planning_items = [
        ("Site Plan Review - 123 Main St", "Commercial development proposal for mixed-use building"),
        ("Conditional Use Permit - Spokane Falls Blvd", "Request for restaurant with outdoor seating"),
        ("Variance Request - Residential Height", "Single-family home requesting height variance"),
        ("Comprehensive Plan Amendment", "Proposed changes to land use designations"),
        ("Subdivision Review - Northside Development", "Review of 45-lot residential subdivision"),
    ]
    
    parks_items = [
        ("Annual Parks Maintenance Report", "Review of 2024 maintenance activities and 2025 plans"),
        ("Trail System Expansion Proposal", "Discussion of new multi-use trail connections"),
        ("Community Center Programming Update", "Review of recreational programming offerings"),
        ("Riverfront Park Improvements", "Phase 2 construction update and timeline"),
    ]
    
    if "Council" in body_name:
        items_pool = council_items
    elif "Plan" in body_name or "Development" in body_name:
        items_pool = planning_items
    else:
        items_pool = parks_items
    
    items = []
    for idx, (title, action_text) in enumerate(items_pool[:6]):
        items.append({
            "EventItemId": event_id * 100 + idx,
            "EventItemTitle": title,
            "EventItemActionText": action_text,
            "EventItemAgendaNumber": f"{idx + 1}.",
            "EventItemMoverName": "Council Member Smith" if idx % 2 == 0 else "Council Member Johnson",
            "EventItemSeconderName": "Council Member Williams" if idx % 2 == 0 else "Council Member Davis",
            "EventItemPassedFlagName": "Pass" if idx < 3 else "",
        })
    
    return items


def seed_meetings(events: list[dict]) -> dict[str, str]:
    """Seed meetings table and return mapping of event_id to meeting_id."""
    dynamodb = get_dynamodb()
    table = dynamodb.Table(MEETINGS_TABLE)
    
    print(f"\n{GREEN}Seeding meetings table...{RESET}")
    
    meeting_ids = {}
    count = 0
    
    for event in events:
        event_id = str(event.get("EventId", ""))
        if not event_id:
            continue
            
        meeting_id = f"meeting_{event_id}"
        meeting_ids[event_id] = meeting_id
        
        # Parse the date
        event_date = event.get("EventDate", "")
        if event_date:
            meeting_date = event_date.split("T")[0]
        else:
            meeting_date = ""
        
        item = {
            "meeting_id": meeting_id,
            "body_name": event.get("EventBodyName", "Unknown Body"),
            "meeting_date": meeting_date,
            "event_time": event.get("EventTime", ""),
            "location": event.get("EventLocation", ""),
            "agenda_status": event.get("EventAgendaStatusName", ""),
            "minutes_status": event.get("EventMinutesStatusName", ""),
            "legistar_event_id": int(event_id),
            "legistar_guid": event.get("EventGuid", ""),
            "ingested_at": datetime.now().isoformat(),
            "last_modified": event.get("EventLastModifiedUtc", ""),
        }
        
        if event.get("EventVideoPath"):
            item["video_url"] = event["EventVideoPath"]
        
        try:
            table.put_item(Item=item)
            count += 1
        except ClientError as e:
            print(f"{RED}  Error inserting meeting {meeting_id}: {e}{RESET}")
    
    print(f"  {GREEN}Inserted {count} meetings{RESET}")
    return meeting_ids


def seed_agenda_items(events: list[dict], meeting_ids: dict[str, str]):
    """Seed agenda items table."""
    dynamodb = get_dynamodb()
    table = dynamodb.Table(AGENDA_TABLE)
    
    print(f"\n{GREEN}Seeding agenda items table...{RESET}")
    
    count = 0
    
    for event in events[:15]:  # Process first 15 events
        event_id = str(event.get("EventId", ""))
        meeting_id = meeting_ids.get(event_id)
        if not meeting_id:
            continue
        
        body_name = event.get("EventBodyName", "")
        items = generate_sample_items_for_meeting(int(event_id), body_name)
        
        for item in items:
            item_id = f"item_{event_id}_{item.get('EventItemId', '')}"
            
            # Assign topics based on title keywords
            title = item.get("EventItemTitle", "").lower()
            if "budget" in title or "appropriation" in title:
                topic = "budget"
                relevance = 4
            elif "zoning" in title or "site plan" in title or "variance" in title:
                topic = "development"
                relevance = 4
            elif "climate" in title or "environment" in title:
                topic = "environment"
                relevance = 5
            elif "public safety" in title or "police" in title:
                topic = "public_safety"
                relevance = 4
            elif "parks" in title or "trail" in title:
                topic = "parks"
                relevance = 3
            elif "consent" in title:
                topic = "procedural"
                relevance = 2
            else:
                topic = "other"
                relevance = 2
            
            meeting_date = event.get("EventDate", "").split("T")[0] if event.get("EventDate") else ""
            
            agenda_item = {
                "item_id": item_id,
                "meeting_id": meeting_id,
                "title": item.get("EventItemTitle", ""),
                "action_text": item.get("EventItemActionText", ""),
                "result": item.get("EventItemPassedFlagName", ""),
                "mover": item.get("EventItemMoverName", ""),
                "seconder": item.get("EventItemSeconderName", ""),
                "agenda_number": str(item.get("EventItemAgendaNumber", "")),
                "topic": topic,
                "relevance": relevance,
                "summary": item.get("EventItemActionText", "")[:200],
                "meeting_date": meeting_date,
                "legistar_item_id": item.get("EventItemId", 0),
            }
            
            agenda_item = {k: v for k, v in agenda_item.items() if v}
            
            try:
                table.put_item(Item=agenda_item)
                count += 1
            except ClientError as e:
                print(f"{RED}    Error inserting item {item_id}: {e}{RESET}")
    
    print(f"  {GREEN}Inserted {count} agenda items{RESET}")


def seed_documents(events: list[dict], meeting_ids: dict[str, str]):
    """Seed documents table with document references."""
    dynamodb = get_dynamodb()
    table = dynamodb.Table(DOCUMENTS_TABLE)
    
    print(f"\n{GREEN}Seeding documents table...{RESET}")
    
    count = 0
    
    for event in events[:15]:
        event_id = str(event.get("EventId", ""))
        meeting_id = meeting_ids.get(event_id)
        
        if not meeting_id:
            continue
        
        if event.get("EventAgendaFile"):
            doc = {
                "document_id": f"doc_agenda_{event_id}",
                "meeting_id": meeting_id,
                "document_type": "agenda",
                "url": event["EventAgendaFile"],
                "title": f"Agenda - {event.get('EventBodyName', '')}",
                "created_at": datetime.now().isoformat(),
            }
            try:
                table.put_item(Item=doc)
                count += 1
            except ClientError as e:
                print(f"{RED}  Error inserting document: {e}{RESET}")
        
        if event.get("EventMinutesFile"):
            doc = {
                "document_id": f"doc_minutes_{event_id}",
                "meeting_id": meeting_id,
                "document_type": "minutes",
                "url": event["EventMinutesFile"],
                "title": f"Minutes - {event.get('EventBodyName', '')}",
                "created_at": datetime.now().isoformat(),
            }
            try:
                table.put_item(Item=doc)
                count += 1
            except ClientError as e:
                print(f"{RED}  Error inserting document: {e}{RESET}")
    
    print(f"  {GREEN}Inserted {count} documents{RESET}")


def print_summary():
    """Print summary of seeded data."""
    dynamodb = get_dynamodb()
    
    print(f"\n{GREEN}=== Seed Summary ==={RESET}")
    
    for table_name in [MEETINGS_TABLE, AGENDA_TABLE, DOCUMENTS_TABLE]:
        table = dynamodb.Table(table_name)
        response = table.scan(Select="COUNT")
        count = response.get("Count", 0)
        print(f"  {table_name}: {count} items")


def main():
    """Main entry point."""
    print(f"{GREEN}=== Spokane Public Brief - Data Seeder ==={RESET}")
    print(f"DynamoDB Endpoint: {DYNAMODB_ENDPOINT}")
    
    # Test connection to DynamoDB
    try:
        dynamodb = get_dynamodb()
        dynamodb.meta.client.list_tables()
    except Exception as e:
        print(f"{RED}Cannot connect to DynamoDB Local at {DYNAMODB_ENDPOINT}{RESET}")
        print(f"Error: {e}")
        print("\nMake sure DynamoDB Local is running:")
        print("  ./scripts/setup-dynamodb-local.sh")
        sys.exit(1)
    
    # Try Legistar API first, fall back to sample data
    events = fetch_legistar_events()
    
    if not events:
        events = generate_sample_events()
    
    if not events:
        print(f"{RED}No events to seed.{RESET}")
        sys.exit(1)
    
    meeting_ids = seed_meetings(events)
    seed_agenda_items(events, meeting_ids)
    seed_documents(events, meeting_ids)
    
    print_summary()
    print(f"\n{GREEN}Seeding complete!{RESET}")


if __name__ == "__main__":
    main()
