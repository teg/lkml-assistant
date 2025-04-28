# Demo 1: Patch Fetching

This demo shows how LKML Assistant fetches patch data from the Patchwork API and stores it in DynamoDB.

## Prerequisites

- AWS CLI installed and configured with access to the deployment account
- Deployed LKML Assistant application

## Demo Steps

### 1. Manually Trigger the Lambda Function

```bash
# Invoke the fetch-patches Lambda function with a small payload
aws lambda invoke \
  --function-name LkmlAssistant-FetchPatches-dev \
  --payload '{"page": 1, "per_page": 5, "process_all_pages": false, "fetch_discussions": false}' \
  fetch-patches-response.json

# Check the response
cat fetch-patches-response.json
```

### 2. View the Stored Patches

```bash
# Get the DynamoDB table name
PATCHES_TABLE=$(aws cloudformation describe-stacks \
  --stack-name LkmlAssistantStack-dev \
  --query "Stacks[0].Outputs[?ExportName=='LkmlAssistant-PatchesTable-dev'].OutputValue" \
  --output text)

# Scan the table for recent entries
aws dynamodb scan \
  --table-name $PATCHES_TABLE \
  --limit 5 \
  --return-consumed-capacity TOTAL
```

### 3. Query Patches by Submitter

```bash
# First, find a submitter from the scanned data
# Then query by that submitter's ID
SUBMITTER_ID=$(aws dynamodb scan \
  --table-name $PATCHES_TABLE \
  --limit 1 \
  --projection-expression "submitterId" \
  --query "Items[0].submitterId.S" \
  --output text)

# Query using GSI1 (SubmitterIndex)
aws dynamodb query \
  --table-name $PATCHES_TABLE \
  --index-name SubmitterIndex \
  --key-condition-expression "gsi1pk = :pk" \
  --expression-attribute-values '{":pk": {"S": "SUBMITTER#'$SUBMITTER_ID'"}}' \
  --limit 5
```

### 4. Check CloudWatch Logs

```bash
# Get the latest log stream
LOG_GROUP="/aws/lambda/LkmlAssistant-FetchPatches-dev"
LOG_STREAM=$(aws logs describe-log-streams \
  --log-group-name $LOG_GROUP \
  --order-by LastEventTime \
  --descending \
  --limit 1 \
  --query "logStreams[0].logStreamName" \
  --output text)

# View the logs
aws logs get-log-events \
  --log-group-name $LOG_GROUP \
  --log-stream-name $LOG_STREAM \
  --limit 20
```

## Expected Results

- The Lambda function should return a 200 status code and a message indicating how many patches were processed
- The DynamoDB table should contain patch data with fields like:
  - `id`: The unique patch identifier
  - `name`: The patch name/title
  - `submitterName`: Who submitted the patch
  - `submittedAt`: When the patch was submitted
  - `status`: The patch status (typically "NEW")
- The CloudWatch logs should show the Lambda function processing patches and storing them in DynamoDB

## Key Features Demonstrated

- Integration with Patchwork API
- Data transformation from API format to database schema
- DynamoDB storage with GSI for different query patterns
- Logging and monitoring implementation