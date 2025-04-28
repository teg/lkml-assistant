# Demo 2: Discussion Fetching

This demo shows how LKML Assistant fetches and stores discussions related to kernel patches.

## Prerequisites

- AWS CLI installed and configured with access to the deployment account
- Deployed LKML Assistant application
- At least one patch already stored in DynamoDB (see Demo 1)

## Demo Steps

### 1. Find a Patch with a Message ID

```bash
# Get the DynamoDB table name
PATCHES_TABLE=$(aws cloudformation describe-stacks \
  --stack-name LkmlAssistantStack-dev \
  --query "Stacks[0].Outputs[?ExportName=='LkmlAssistant-PatchesTable-dev'].OutputValue" \
  --output text)

# Scan the table to find a patch with a messageId
aws dynamodb scan \
  --table-name $PATCHES_TABLE \
  --filter-expression "attribute_exists(messageId)" \
  --projection-expression "id,messageId,name" \
  --limit 5
```

### 2. Manually Trigger the Discussion Fetch Lambda

```bash
# Use a patch ID and message ID from the previous step
PATCH_ID="<PATCH_ID_FROM_STEP_1>"
MESSAGE_ID="<MESSAGE_ID_FROM_STEP_1>"

# Invoke the fetch-discussions Lambda function
aws lambda invoke \
  --function-name LkmlAssistant-FetchDiscussions-dev \
  --payload '{"patch_id": "'$PATCH_ID'", "message_id": "'$MESSAGE_ID'"}' \
  fetch-discussions-response.json

# Check the response
cat fetch-discussions-response.json
```

### 3. View the Stored Discussions

```bash
# Get the discussions table name
DISCUSSIONS_TABLE=$(aws cloudformation describe-stacks \
  --stack-name LkmlAssistantStack-dev \
  --query "Stacks[0].Outputs[?ExportName=='LkmlAssistant-DiscussionsTable-dev'].OutputValue" \
  --output text)

# Query discussions for the specified patch
aws dynamodb query \
  --table-name $DISCUSSIONS_TABLE \
  --index-name PatchIndex \
  --key-condition-expression "gsi1pk = :pk" \
  --expression-attribute-values '{":pk": {"S": "PATCH#'$PATCH_ID'"}}' \
  --limit 10
```

### 4. Examine Discussion Threading

```bash
# Find discussions that are part of a thread (replies)
aws dynamodb scan \
  --table-name $DISCUSSIONS_TABLE \
  --filter-expression "attribute_exists(parentId)" \
  --projection-expression "id,parentId,subject,author" \
  --limit 5
```

### 5. View Discussion by Author

```bash
# First, get an author from a discussion
AUTHOR_EMAIL=$(aws dynamodb scan \
  --table-name $DISCUSSIONS_TABLE \
  --limit 1 \
  --projection-expression "authorEmail" \
  --query "Items[0].authorEmail.S" \
  --output text)

# Query using GSI3 (AuthorIndex)
aws dynamodb query \
  --table-name $DISCUSSIONS_TABLE \
  --index-name AuthorIndex \
  --key-condition-expression "gsi3pk = :pk" \
  --expression-attribute-values '{":pk": {"S": "AUTHOR#'$AUTHOR_EMAIL'"}}' \
  --limit 5
```

### 6. Check the Updated Patch Record

```bash
# Check if the patch record has been updated with the discussion count
aws dynamodb get-item \
  --table-name $PATCHES_TABLE \
  --key '{"id": {"S": "'$PATCH_ID'"}}'
```

## Expected Results

- The Lambda function should return a success response
- The Discussions table should contain email message data with fields like:
  - `id`: The unique discussion identifier
  - `patchId`: The associated patch ID
  - `subject`: Email subject line
  - `author`: Who wrote the message
  - `content`: The email content
  - `threadId`: Email thread ID
  - `parentId`: For replies, the ID of the parent message
- The Patch record should be updated with a `discussionCount` showing how many related messages exist
- You should be able to see threaded discussions (messages and replies)

## Key Features Demonstrated

- Integration with lore.kernel.org to fetch email discussions
- Email threading and relationship tracking
- Cross-table data updates (updating patch records with discussion counts)
- Use of multiple DynamoDB GSIs for different query patterns
- Bidirectional linking between patches and discussions