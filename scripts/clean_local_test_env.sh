#!/bin/bash
set -e

# Script to clean up the local test environment

# Colors for console output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Cleaning up local test environment...${NC}"

# Set environment variables for AWS CLI to point to local services
export AWS_ENDPOINT_URL=http://localhost:4566
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

# Remove DynamoDB tables
echo -e "${BLUE}Removing DynamoDB tables...${NC}"
aws dynamodb delete-table --endpoint-url http://localhost:8000 --table-name LkmlAssistant-Patches-test || true
aws dynamodb delete-table --endpoint-url http://localhost:8000 --table-name LkmlAssistant-Discussions-test || true

# Remove Lambda functions
echo -e "${BLUE}Removing Lambda functions...${NC}"
aws lambda delete-function --endpoint-url http://localhost:4566 --function-name LkmlAssistant-FetchPatches-test || true
aws lambda delete-function --endpoint-url http://localhost:4566 --function-name LkmlAssistant-FetchDiscussions-test || true
aws lambda delete-function --endpoint-url http://localhost:4566 --function-name LkmlAssistant-RefreshDiscussions-test || true

# Clean up temporary files
echo -e "${BLUE}Cleaning up temporary files...${NC}"
rm -rf .tmp/lambda || true

# Stop Podman containers (optional - you might want to keep them running for multiple test runs)
if [ "$1" = "--stop-containers" ]; then
    echo -e "${BLUE}Stopping Podman containers...${NC}"
    podman stop lkml-assistant-dynamodb && podman rm lkml-assistant-dynamodb || true
fi

echo -e "${GREEN}Local test environment has been cleaned up!${NC}"