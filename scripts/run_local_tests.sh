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

# Upload the Lambda code to LocalStack
echo -e "${BLUE}Preparing Lambda functions...${NC}"
mkdir -p .tmp/lambda
(cd src && zip -r ../.tmp/lambda/fetch-patches.zip functions repositories utils models)

# Run the actual tests
echo -e "${BLUE}Running pytest integration tests...${NC}"
python -m pytest tests/integration -v

# Cleanup after tests
echo -e "${BLUE}Cleaning up test environment...${NC}"
./scripts/clean_local_test_env.sh --stop-containers

echo -e "${GREEN}Local integration tests completed!${NC}"