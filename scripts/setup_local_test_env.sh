#!/bin/bash
set -e

# Script to set up a local test environment using docker-compose

# Colors for console output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Setting up local test environment for LKML Assistant...${NC}"

# Check for Podman 
if ! command -v podman &> /dev/null; then
    echo -e "${RED}Error: Podman is not installed. Please install Podman first.${NC}"
    exit 1
fi

# Start the local services (DynamoDB only for simplicity)
echo -e "${BLUE}Starting local AWS services with Podman...${NC}"
podman run -d --name lkml-assistant-dynamodb -p 8000:8000 amazon/dynamodb-local:latest -jar DynamoDBLocal.jar -sharedDb -inMemory

# Wait for services to be ready
echo -e "${BLUE}Waiting for services to be ready...${NC}"
sleep 5

# Set environment variables for AWS CLI to point to local services
export AWS_ENDPOINT_URL=http://localhost:4566
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

# Create DynamoDB tables for Patches and Discussions
echo -e "${BLUE}Creating DynamoDB tables...${NC}"

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
    --billing-mode PAY_PER_REQUEST

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
    --billing-mode PAY_PER_REQUEST

# Set up Lambda functions in LocalStack (if needed)
echo -e "${BLUE}Setting up Lambda functions in LocalStack...${NC}"

# Zip up the Lambda source code
mkdir -p .tmp/lambda
(cd src && zip -r ../.tmp/lambda/fetch-patches.zip functions repositories utils models)

# Create Lambda functions in LocalStack
aws lambda create-function \
    --endpoint-url http://localhost:4566 \
    --function-name LkmlAssistant-FetchPatches-test \
    --runtime python3.9 \
    --handler src.functions.fetch_patches.index.handler \
    --zip-file fileb://.tmp/lambda/fetch-patches.zip \
    --environment "Variables={PATCHES_TABLE_NAME=LkmlAssistant-Patches-test,FETCH_DISCUSSIONS_LAMBDA=LkmlAssistant-FetchDiscussions-test,ENVIRONMENT=test,LOG_LEVEL=DEBUG}" \
    --role arn:aws:iam::000000000000:role/lambda-role

echo -e "${GREEN}Local test environment is ready!${NC}"
echo -e "${YELLOW}Note: Services are running in Docker containers. Use docker-compose down to stop them when done.${NC}"
echo -e "${YELLOW}To use the local environment, set these environment variables:${NC}"
echo -e "${YELLOW}export AWS_ENDPOINT_URL=http://localhost:4566${NC}"
echo -e "${YELLOW}export DYNAMODB_ENDPOINT=http://localhost:8000${NC}"
echo -e "${YELLOW}export AWS_ACCESS_KEY_ID=test${NC}"
echo -e "${YELLOW}export AWS_SECRET_ACCESS_KEY=test${NC}"
echo -e "${YELLOW}export AWS_DEFAULT_REGION=us-east-1${NC}"