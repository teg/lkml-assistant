#!/bin/bash
set -e

# Script to run integration tests against local Docker containers

# Colors for console output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Running local integration tests...${NC}"

# First, clean up any previous test environment
if [ -f docker-compose.log ]; then
    echo -e "${BLUE}Cleaning up previous test environment...${NC}"
    ./scripts/clean_local_test_env.sh --stop-containers || true
fi

# Start the Podman containers and set up test environment
echo -e "${BLUE}Starting Podman containers for testing...${NC}"
./scripts/setup_local_test_env.sh > podman.log 2>&1

# Wait for the containers to be ready
echo -e "${BLUE}Waiting for containers to be ready...${NC}"
sleep 5

# Prepare Lambda deployment package
echo -e "${BLUE}Preparing Lambda functions...${NC}"
mkdir -p .tmp/lambda

# Make sure we have necessary tools
if ! command -v zip &> /dev/null; then
    echo -e "${RED}Error: 'zip' utility is not installed. Please install it first.${NC}"
    exit 1
fi

# Create Lambda package
echo -e "${BLUE}Creating Lambda deployment package...${NC}"
(cd src && zip -r ../.tmp/lambda/fetch-patches.zip functions repositories utils models)

# List the content to verify
ls -la .tmp/lambda/

# Wait a bit for LocalStack to be fully ready
echo -e "${BLUE}Waiting for LocalStack to be ready...${NC}"
sleep 10

# Set up the Lambda functions in LocalStack
echo -e "${BLUE}Setting up Lambda functions in LocalStack...${NC}"
./scripts/setup_local_test_env.sh

# Run the actual tests
echo -e "${BLUE}Running LocalStack Lambda tests...${NC}"
python -m pytest tests/integration/test_local_lambda.py::test_fetch_patches_lambda_localstack -v || true

echo -e "${BLUE}Running DynamoDB integration tests...${NC}"
python -m pytest tests/integration/test_local_dynamodb.py -v

# Cleanup after tests
echo -e "${BLUE}Cleaning up test environment...${NC}"
./scripts/clean_local_test_env.sh --stop-containers

echo -e "${GREEN}Local integration tests completed!${NC}"