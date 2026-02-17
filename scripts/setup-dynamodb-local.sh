#!/bin/bash
# Setup DynamoDB Local for Spokane Public Brief development
# Creates all 3 tables with their GSIs matching infra/main.tf

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DYNAMODB_DIR="$PROJECT_DIR/dynamodb-local"
DYNAMODB_PORT="${DYNAMODB_PORT:-8000}"
DYNAMODB_ENDPOINT="http://localhost:$DYNAMODB_PORT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Spokane Public Brief - DynamoDB Local Setup ===${NC}"

# Check if Java is available
if ! command -v java &> /dev/null; then
    echo -e "${RED}Error: Java is not installed. Please install JRE first.${NC}"
    exit 1
fi

# Check if DynamoDB Local JAR exists
if [[ ! -f "$DYNAMODB_DIR/DynamoDBLocal.jar" ]]; then
    echo -e "${RED}Error: DynamoDBLocal.jar not found at $DYNAMODB_DIR${NC}"
    echo "Please download from https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html"
    exit 1
fi

# Check if DynamoDB Local is already running
if lsof -i:$DYNAMODB_PORT &> /dev/null; then
    echo -e "${YELLOW}DynamoDB Local already running on port $DYNAMODB_PORT${NC}"
else
    echo -e "${GREEN}Starting DynamoDB Local on port $DYNAMODB_PORT...${NC}"
    cd "$DYNAMODB_DIR"
    java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -port $DYNAMODB_PORT -inMemory &
    DYNAMODB_PID=$!
    echo "DynamoDB Local started with PID $DYNAMODB_PID"
    
    # Wait for it to be ready
    echo "Waiting for DynamoDB Local to be ready..."
    for i in {1..30}; do
        if curl -s "$DYNAMODB_ENDPOINT" > /dev/null 2>&1; then
            echo -e "${GREEN}DynamoDB Local is ready!${NC}"
            break
        fi
        sleep 0.5
    done
fi

# Function to create table (ignores ResourceInUseException if table exists)
create_table() {
    local table_def="$1"
    local table_name=$(echo "$table_def" | python3 -c "import sys,json; print(json.load(sys.stdin)['TableName'])")
    
    echo -e "Creating table: ${YELLOW}$table_name${NC}"
    
    if aws dynamodb describe-table --table-name "$table_name" --endpoint-url "$DYNAMODB_ENDPOINT" > /dev/null 2>&1; then
        echo -e "  ${YELLOW}Table already exists, skipping${NC}"
    else
        aws dynamodb create-table --cli-input-json "$table_def" --endpoint-url "$DYNAMODB_ENDPOINT" > /dev/null
        echo -e "  ${GREEN}Created!${NC}"
    fi
}

# Create meetings table with body-date-index GSI
echo -e "\n${GREEN}Creating DynamoDB tables...${NC}"

create_table '{
    "TableName": "spokane-public-brief-meetings-local",
    "AttributeDefinitions": [
        {"AttributeName": "meeting_id", "AttributeType": "S"},
        {"AttributeName": "body_name", "AttributeType": "S"},
        {"AttributeName": "meeting_date", "AttributeType": "S"}
    ],
    "KeySchema": [
        {"AttributeName": "meeting_id", "KeyType": "HASH"}
    ],
    "GlobalSecondaryIndexes": [
        {
            "IndexName": "body-date-index",
            "KeySchema": [
                {"AttributeName": "body_name", "KeyType": "HASH"},
                {"AttributeName": "meeting_date", "KeyType": "RANGE"}
            ],
            "Projection": {"ProjectionType": "ALL"}
        }
    ],
    "BillingMode": "PAY_PER_REQUEST"
}'

# Create agenda_items table with meeting-index GSI
create_table '{
    "TableName": "spokane-public-brief-agenda-items-local",
    "AttributeDefinitions": [
        {"AttributeName": "item_id", "AttributeType": "S"},
        {"AttributeName": "meeting_id", "AttributeType": "S"}
    ],
    "KeySchema": [
        {"AttributeName": "item_id", "KeyType": "HASH"}
    ],
    "GlobalSecondaryIndexes": [
        {
            "IndexName": "meeting-index",
            "KeySchema": [
                {"AttributeName": "meeting_id", "KeyType": "HASH"}
            ],
            "Projection": {"ProjectionType": "ALL"}
        }
    ],
    "BillingMode": "PAY_PER_REQUEST"
}'

# Create documents table (no GSI)
create_table '{
    "TableName": "spokane-public-brief-documents-local",
    "AttributeDefinitions": [
        {"AttributeName": "document_id", "AttributeType": "S"}
    ],
    "KeySchema": [
        {"AttributeName": "document_id", "KeyType": "HASH"}
    ],
    "BillingMode": "PAY_PER_REQUEST"
}'

echo -e "\n${GREEN}=== Setup Complete ===${NC}"
echo -e "DynamoDB Local: $DYNAMODB_ENDPOINT"
echo -e "\nTables created:"
aws dynamodb list-tables --endpoint-url "$DYNAMODB_ENDPOINT" --output table
