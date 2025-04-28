#!/bin/bash
set -e

# Script to run direct Lambda invocation tests without requiring LocalStack

# Colors for console output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Running direct Lambda invocation tests...${NC}"

# First, clean up any previous test environment completely
echo -e "${BLUE}Cleaning up previous test environment...${NC}"

# Check for and remove any pods related to lkml-assistant
for pod in $(podman pod ps --format "{{.Id}}" | grep -v "INFRA ID"); do
    if podman pod inspect $pod | grep -q "lkml-assistant"; then
        echo -e "${YELLOW}Removing pod: $pod${NC}"
        podman pod rm --force $pod >/dev/null 2>&1 || true
    fi
done

# Stop and remove all lkml-assistant related containers
podman stop $(podman ps -a | grep lkml-assistant | awk '{print $1}') >/dev/null 2>&1 || true
podman rm -f $(podman ps -a | grep lkml-assistant | awk '{print $1}') >/dev/null 2>&1 || true

# Double check that the dynamodb container is completely gone
if podman ps -a | grep -q "lkml-assistant"; then
    echo -e "${RED}Failed to remove all containers. Please manually clean up with these commands:${NC}"
    echo -e "${YELLOW}podman pod rm --force \$(podman pod ps --format \"{{.Id}}\")${NC}"
    echo -e "${YELLOW}podman rm -f \$(podman ps -a | grep lkml-assistant | awk '{print \$1}')${NC}"
    exit 1
fi

# Start just the DynamoDB container for testing
echo -e "${BLUE}Starting DynamoDB container for testing...${NC}"
if ! podman run -d --name lkml-assistant-dynamodb -p 8000:8000 amazon/dynamodb-local:latest -jar DynamoDBLocal.jar -sharedDb -inMemory; then
    echo -e "${RED}Failed to start DynamoDB container. Exiting.${NC}"
    exit 1
fi

# Wait for the container to be ready
echo -e "${BLUE}Waiting for container to be ready...${NC}"
sleep 5

# Set up the DynamoDB tables
echo -e "${BLUE}Setting up DynamoDB tables...${NC}"
# Set environment variables for AWS CLI
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

# Create Patches table
aws dynamodb create-table \
    --endpoint-url http://localhost:8000 \
    --table-name LkmlAssistant-Patches-test \
    --attribute-definitions \
        AttributeName=id,AttributeType=S \
        AttributeName=gsi1pk,AttributeType=S \
        AttributeName=gsi1sk,AttributeType=S \
        AttributeName=gsi2pk,AttributeType=S \
        AttributeName=gsi2sk,AttributeType=S \
        AttributeName=gsi3pk,AttributeType=S \
        AttributeName=gsi3sk,AttributeType=S \
    --key-schema \
        AttributeName=id,KeyType=HASH \
    --global-secondary-indexes \
        "[
            {
                \"IndexName\": \"SubmitterIndex\",
                \"KeySchema\": [
                    {\"AttributeName\": \"gsi1pk\", \"KeyType\": \"HASH\"},
                    {\"AttributeName\": \"gsi1sk\", \"KeyType\": \"RANGE\"}
                ],
                \"Projection\": {\"ProjectionType\": \"ALL\"}
            },
            {
                \"IndexName\": \"SeriesIndex\",
                \"KeySchema\": [
                    {\"AttributeName\": \"gsi2pk\", \"KeyType\": \"HASH\"},
                    {\"AttributeName\": \"gsi2sk\", \"KeyType\": \"RANGE\"}
                ],
                \"Projection\": {\"ProjectionType\": \"ALL\"}
            },
            {
                \"IndexName\": \"StatusIndex\",
                \"KeySchema\": [
                    {\"AttributeName\": \"gsi3pk\", \"KeyType\": \"HASH\"},
                    {\"AttributeName\": \"gsi3sk\", \"KeyType\": \"RANGE\"}
                ],
                \"Projection\": {\"ProjectionType\": \"ALL\"}
            }
        ]" \
    --billing-mode PAY_PER_REQUEST || true

# Create Discussions table
aws dynamodb create-table \
    --endpoint-url http://localhost:8000 \
    --table-name LkmlAssistant-Discussions-test \
    --attribute-definitions \
        AttributeName=id,AttributeType=S \
        AttributeName=timestamp,AttributeType=S \
        AttributeName=gsi1pk,AttributeType=S \
        AttributeName=gsi1sk,AttributeType=S \
        AttributeName=gsi2pk,AttributeType=S \
        AttributeName=gsi2sk,AttributeType=S \
        AttributeName=gsi3pk,AttributeType=S \
        AttributeName=gsi3sk,AttributeType=S \
    --key-schema \
        AttributeName=id,KeyType=HASH \
        AttributeName=timestamp,KeyType=RANGE \
    --global-secondary-indexes \
        "[
            {
                \"IndexName\": \"PatchIndex\",
                \"KeySchema\": [
                    {\"AttributeName\": \"gsi1pk\", \"KeyType\": \"HASH\"},
                    {\"AttributeName\": \"gsi1sk\", \"KeyType\": \"RANGE\"}
                ],
                \"Projection\": {\"ProjectionType\": \"ALL\"}
            },
            {
                \"IndexName\": \"ThreadIndex\",
                \"KeySchema\": [
                    {\"AttributeName\": \"gsi2pk\", \"KeyType\": \"HASH\"},
                    {\"AttributeName\": \"gsi2sk\", \"KeyType\": \"RANGE\"}
                ],
                \"Projection\": {\"ProjectionType\": \"ALL\"}
            },
            {
                \"IndexName\": \"AuthorIndex\",
                \"KeySchema\": [
                    {\"AttributeName\": \"gsi3pk\", \"KeyType\": \"HASH\"},
                    {\"AttributeName\": \"gsi3sk\", \"KeyType\": \"RANGE\"}
                ],
                \"Projection\": {\"ProjectionType\": \"ALL\"}
            }
        ]" \
    --billing-mode PAY_PER_REQUEST || true

# Wait for tables to be created
sleep 2

# Run just the direct Lambda invocation tests
echo -e "${BLUE}Running direct Lambda invocation tests...${NC}"
/Library/Frameworks/Python.framework/Versions/3.9/bin/python3 -m pytest tests/integration/test_local_lambda.py::test_fetch_patches_lambda_direct -v

# Cleanup after tests
echo -e "${BLUE}Cleaning up test environment...${NC}"
podman stop lkml-assistant-dynamodb || true
podman rm lkml-assistant-dynamodb || true

echo -e "${GREEN}Direct Lambda invocation tests completed!${NC}"