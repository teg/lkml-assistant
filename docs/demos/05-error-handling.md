# Demo 5: Error Handling and Monitoring

This demo shows how LKML Assistant handles errors and provides monitoring capabilities.

## Prerequisites

- AWS CLI installed and configured with access to the deployment account
- Deployed LKML Assistant application

## Demo Steps

### 1. Examine the Dead Letter Queue

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

### 2. Trigger an Error (Intentionally)

```bash
# Invoke the fetch-discussions Lambda with an invalid messageId
aws lambda invoke \
  --function-name LkmlAssistant-FetchDiscussions-dev \
  --payload '{"patch_id": "123456", "message_id": "this-is-not-a-valid-message-id"}' \
  error-response.json

# Check the response
cat error-response.json
```

### 3. View CloudWatch Logs for Errors

```bash
# Get the latest log stream
LOG_GROUP="/aws/lambda/LkmlAssistant-FetchDiscussions-dev"
LOG_STREAM=$(aws logs describe-log-streams \
  --log-group-name $LOG_GROUP \
  --order-by LastEventTime \
  --descending \
  --limit 1 \
  --query "logStreams[0].logStreamName" \
  --output text)

# View the logs focusing on errors
aws logs get-log-events \
  --log-group-name $LOG_GROUP \
  --log-stream-name $LOG_STREAM \
  --filter-pattern "ERROR" \
  --limit 10
```

### 4. Check CloudWatch Alarms

```bash
# List all alarms with the LkmlAssistant prefix
aws cloudwatch describe-alarms \
  --alarm-name-prefix LkmlAssistant \
  --query "MetricAlarms[].{Name:AlarmName,State:StateValue,Metric:MetricName}"
```

### 5. Explore CloudWatch Dashboard

```bash
# Get the dashboard URL
DASHBOARD_URL=$(aws cloudformation describe-stacks \
  --stack-name LkmlAssistantStack-dev \
  --query "Stacks[0].Outputs[?ExportName=='LkmlAssistant-Dashboard-dev'].OutputValue" \
  --output text)

echo "Visit the CloudWatch Dashboard at: $DASHBOARD_URL"

# Alternatively, describe the dashboard widgets
aws cloudwatch get-dashboard \
  --dashboard-name LkmlAssistant-dev \
  --query "DashboardBody" | jq -r | jq '.widgets | map(.properties.title)'
```

### 6. Check Lambda Function Metrics

```bash
# Get invocation metrics for the fetch-patches Lambda
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --start-time "$(date -u -v-1d +"%Y-%m-%dT%H:%M:%SZ")" \
  --end-time "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
  --period 3600 \
  --statistics Sum \
  --dimensions Name=FunctionName,Value=LkmlAssistant-FetchPatches-dev

# Get error metrics for the fetch-patches Lambda
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --start-time "$(date -u -v-1d +"%Y-%m-%dT%H:%M:%SZ")" \
  --end-time "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
  --period 3600 \
  --statistics Sum \
  --dimensions Name=FunctionName,Value=LkmlAssistant-FetchPatches-dev
```

### 7. Examine Retry Configuration

```bash
# View the EventBridge rule target configuration to see retry settings
aws events list-targets-by-rule \
  --rule LkmlAssistant-FetchPatchesHourly \
  --query "Targets[].{RetryAttempts:RetryPolicy.MaximumRetryAttempts, MaxEventAge:RetryPolicy.MaximumEventAgeInSeconds}"
```

## Expected Results

- The Dead Letter Queue should capture failed executions after retries
- CloudWatch logs should show error handling and tracing
- CloudWatch Dashboard should display metrics for Lambda functions, DynamoDB tables, and the DLQ
- CloudWatch Alarms should monitor for DLQ messages and other error conditions
- The Lambda invocation with an invalid message ID should fail gracefully
- You should see retry configuration for Lambda invocations from EventBridge

## Key Features Demonstrated

- Dead Letter Queue for failed executions
- CloudWatch Alarms for error detection
- Error handling in Lambda functions
- Logging with structured error information
- Retry policies for increased resilience
- Consolidated CloudWatch Dashboard
- Lambda function metrics tracking