# LKML Assistant Demo Guide

This directory contains demonstrations of the LKML Assistant's features and functionality. Each demo focuses on a specific aspect of the system and provides step-by-step instructions for exploring and testing the functionality.

## Available Demos

1. **[Patch Fetching](./01-fetch-patches.md)** - How the system fetches and stores Linux kernel patches
2. **[Discussion Fetching](./02-fetch-discussions.md)** - How the system retrieves and organizes discussion threads
3. **[Scheduled Operations](./03-scheduled-operations.md)** - How automated data collection is configured
4. **[Advanced Queries](./04-advanced-queries.md)** - How to retrieve specific information using advanced query patterns
5. **[Error Handling and Monitoring](./05-error-handling.md)** - How the system handles errors and provides monitoring
6. **[Multi-Environment Support](./06-multi-environment.md)** - How the system supports different deployment environments

## Prerequisites

Before running these demos, ensure you have:

1. AWS CLI installed and configured with appropriate permissions
2. Access to the AWS account where LKML Assistant is deployed
3. The application successfully deployed (at least in the dev environment)
4. Basic familiarity with AWS services (Lambda, DynamoDB, CloudWatch)

## Demo Order

The demos are numbered in a logical progression that follows the system's data flow and feature set. It's recommended to go through them in order, as later demos may depend on data created in earlier ones.

## General Tips

- All commands in the demos are designed to be run from a Unix-like terminal (macOS, Linux, or WSL on Windows)
- Commands use environment variables to store intermediate values for reuse in subsequent commands
- Adjust region or account-specific values as needed for your environment
- For convenience, the demos use the AWS CLI, but the same operations could be performed via the AWS Console

## Viewing Results

Most demo commands output JSON data. For better readability, you can pipe the output through tools like `jq` or use the `--output table` parameter when supported:

```bash
# Example with jq
aws dynamodb scan --table-name LkmlAssistant-Patches-dev --limit 5 | jq '.Items[]'

# Example with table output
aws lambda list-functions --query "Functions[?starts_with(FunctionName, 'LkmlAssistant')].FunctionName" --output table
```