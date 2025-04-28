# Demo 3: Scheduled Operations

This demo shows how LKML Assistant automatically keeps its data fresh using scheduled operations via Amazon EventBridge.

## Prerequisites

- AWS CLI installed and configured with access to the deployment account
- Deployed LKML Assistant application

## Demo Steps

### 1. Examine the EventBridge Rules

```bash
# List all EventBridge rules with the LkmlAssistant prefix
aws events list-rules \
  --name-prefix LkmlAssistant

# Get details of the hourly rule
aws events describe-rule \
  --name LkmlAssistant-FetchPatchesHourly
```

### 2. View Rule Targets

```bash
# View the targets for the hourly rule
aws events list-targets-by-rule \
  --rule LkmlAssistant-FetchPatchesHourly

# View the targets for the daily rule
aws events list-targets-by-rule \
  --rule LkmlAssistant-FetchPatchesDaily
```

### 3. Manually Trigger a Scheduled Rule

```bash
# Get the ARN of the fetch-patches Lambda function
LAMBDA_ARN=$(aws lambda get-function \
  --function-name LkmlAssistant-FetchPatches-dev \
  --query "Configuration.FunctionArn" \
  --output text)

# Put an event to the EventBridge to trigger the hourly rule
aws events put-events \
  --entries '[{
    "Source": "scheduled.hourly",
    "DetailType": "Scheduled Event",
    "Resources": ["'$LAMBDA_ARN'"],
    "Detail": "{\"source\":\"scheduled.hourly\",\"time\":\"'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'\",\"page\":1,\"per_page\":5,\"process_all_pages\":false,\"fetch_discussions\":true}"
  }]'
```

### 4. Check the Dead Letter Queue

```bash
# Get the Dead Letter Queue URL
DLQ_URL=$(aws sqs get-queue-url \
  --queue-name LkmlAssistant-DLQ \
  --query "QueueUrl" \
  --output text)

# Check if there are any messages in the DLQ
aws sqs get-queue-attributes \
  --queue-url $DLQ_URL \
  --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible
```

### 5. Examine CloudWatch Dashboard

```bash
# Get the dashboard URL
DASHBOARD_URL=$(aws cloudformation describe-stacks \
  --stack-name LkmlAssistantStack-dev \
  --query "Stacks[0].Outputs[?ExportName=='LkmlAssistant-Dashboard-dev'].OutputValue" \
  --output text)

echo "Visit the CloudWatch Dashboard at: $DASHBOARD_URL"
```

### 6. Verify Recent Data Updates

```bash
# Get the DynamoDB table name
PATCHES_TABLE=$(aws cloudformation describe-stacks \
  --stack-name LkmlAssistantStack-dev \
  --query "Stacks[0].Outputs[?ExportName=='LkmlAssistant-PatchesTable-dev'].OutputValue" \
  --output text)

# Check for recently updated patches (in the last hour)
TIMESTAMP=$(date -u -v-1H +"%Y-%m-%dT%H:%M:%SZ")
aws dynamodb scan \
  --table-name $PATCHES_TABLE \
  --filter-expression "lastUpdatedAt > :timestamp" \
  --expression-attribute-values '{":timestamp": {"S": "'$TIMESTAMP'"}}' \
  --projection-expression "id,name,lastUpdatedAt" \
  --limit 5
```

## Expected Results

- You should see three EventBridge rules:
  1. `LkmlAssistant-FetchPatchesHourly` (runs every hour)
  2. `LkmlAssistant-FetchPatchesDaily` (runs at 3:00 AM UTC)
  3. `LkmlAssistant-RefreshDiscussionsWeekly` (runs Sundays at 4:30 AM UTC)
- The targets for these rules should point to the relevant Lambda functions
- The DLQ should ideally be empty (no failed executions)
- The CloudWatch Dashboard should show metrics for:
  - Lambda invocations
  - Lambda errors
  - DynamoDB read/write capacity
  - DLQ message counts
- You should see records in the Patches table with recent `lastUpdatedAt` timestamps

## Key Features Demonstrated

- Automated data collection via CloudWatch Events/EventBridge
- Scheduled operations configuration
- Error handling via Dead Letter Queue
- CloudWatch Dashboards for monitoring
- Continuous data refreshing strategy
- Resource isolation with environment-specific naming