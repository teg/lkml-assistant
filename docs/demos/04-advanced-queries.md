# Demo 4: Advanced Queries

This demo shows how to use advanced query patterns in LKML Assistant to find specific information and analyze the data.

## Prerequisites

- AWS CLI installed and configured with access to the deployment account
- Deployed LKML Assistant application with data loaded (see previous demos)

## Demo Steps

### 1. Query Patches by Status

```bash
# Get the DynamoDB table name
PATCHES_TABLE=$(aws cloudformation describe-stacks \
  --stack-name LkmlAssistantStack-dev \
  --query "Stacks[0].Outputs[?ExportName=='LkmlAssistant-PatchesTable-dev'].OutputValue" \
  --output text)

# Query patches with "NEW" status
aws dynamodb query \
  --table-name $PATCHES_TABLE \
  --index-name StatusIndex \
  --key-condition-expression "gsi3pk = :status" \
  --expression-attribute-values '{":status": {"S": "STATUS#NEW"}}' \
  --limit 5
```

### 2. Find Patches in a Series

```bash
# First, find a series ID from a patch
SERIES_INFO=$(aws dynamodb scan \
  --table-name $PATCHES_TABLE \
  --filter-expression "attribute_exists(seriesId)" \
  --projection-expression "id,seriesId,seriesName" \
  --limit 1)

SERIES_ID=$(echo $SERIES_INFO | jq -r '.Items[0].seriesId.S')
SERIES_NAME=$(echo $SERIES_INFO | jq -r '.Items[0].seriesName.S')

echo "Found series: $SERIES_NAME (ID: $SERIES_ID)"

# Query all patches in the same series
aws dynamodb query \
  --table-name $PATCHES_TABLE \
  --index-name SeriesIndex \
  --key-condition-expression "gsi2pk = :series" \
  --expression-attribute-values '{":series": {"S": "SERIES#'$SERIES_ID'"}}' \
  --limit 10
```

### 3. Find Patches with Active Discussions

```bash
# Find patches with discussions
aws dynamodb scan \
  --table-name $PATCHES_TABLE \
  --filter-expression "discussionCount > :zero" \
  --expression-attribute-values '{":zero": {"N": "0"}}' \
  --projection-expression "id,name,discussionCount" \
  --limit 5
```

### 4. Find Discussion Threads

```bash
# Get the discussions table name
DISCUSSIONS_TABLE=$(aws cloudformation describe-stacks \
  --stack-name LkmlAssistantStack-dev \
  --query "Stacks[0].Outputs[?ExportName=='LkmlAssistant-DiscussionsTable-dev'].OutputValue" \
  --output text)

# Find a thread ID from a discussion
THREAD_INFO=$(aws dynamodb scan \
  --table-name $DISCUSSIONS_TABLE \
  --projection-expression "id,threadId,subject" \
  --limit 1)

THREAD_ID=$(echo $THREAD_INFO | jq -r '.Items[0].threadId.S')
SUBJECT=$(echo $THREAD_INFO | jq -r '.Items[0].subject.S')

echo "Found thread: $SUBJECT (Thread ID: $THREAD_ID)"

# Query all messages in the same thread
aws dynamodb query \
  --table-name $DISCUSSIONS_TABLE \
  --index-name ThreadIndex \
  --key-condition-expression "gsi2pk = :thread" \
  --expression-attribute-values '{":thread": {"S": "THREAD#'$THREAD_ID'"}}' \
  --limit 10
```

### 5. Find Prolific Submitters

```bash
# Scan to count patches by submitter
# Note: In a production app, this would be done with analytics, not a scan
aws dynamodb scan \
  --table-name $PATCHES_TABLE \
  --projection-expression "submitterName,submitterId" > submitters.json

# Process with jq to find top submitters
cat submitters.json | jq '.Items | group_by(.submitterName.S) | map({submitter: .[0].submitterName.S, count: length}) | sort_by(.count) | reverse | .[0:5]'
```

### 6. Find Recent Activity

```bash
# Get patches from the last 24 hours
YESTERDAY=$(date -u -v-1d +"%Y-%m-%dT%H:%M:%SZ")
aws dynamodb scan \
  --table-name $PATCHES_TABLE \
  --filter-expression "submittedAt > :yesterday" \
  --expression-attribute-values '{":yesterday": {"S": "'$YESTERDAY'"}}' \
  --projection-expression "id,name,submitterName,submittedAt" \
  --limit 10
```

## Expected Results

- You should be able to query patches by their status
- You should see all patches that belong to the same series
- You should identify patches that have active discussions
- You should be able to retrieve all messages in a discussion thread
- You should identify the most active submitters
- You should see the most recent activity in the kernel mailing list

## Key Features Demonstrated

- Use of DynamoDB Global Secondary Indexes (GSIs)
- Complex query patterns
- Data relationships (series, threads)
- Activity tracking
- Time-based filtering
- Multi-field projections
- Attribute filtering