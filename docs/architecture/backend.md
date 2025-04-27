# Backend Architecture

This document details the backend architecture of the LKML Assistant.

## AWS Services

The backend is built on a suite of AWS serverless services:

### AWS Lambda

Lambda functions form the core of the backend processing:

- **FetchPatches**: Retrieves patch data from the Patchwork API
- **FetchDiscussions**: Retrieves discussion data from lore.kernel.org
- **RefreshDiscussions**: Periodically refreshes discussion data for recent patches
- **API Handlers** (Planned): For handling API requests from the frontend

Lambda functions are configured with:
- Python 3.9 runtime
- Memory allocation based on environment (512MB for dev, 1024MB for prod)
- Proper timeout configuration (300 seconds)
- Tracing enabled in production
- Environment-specific logging levels

### DynamoDB

DynamoDB provides the data storage layer:

- **Patches Table**: Stores metadata about patches
- **Discussions Table**: Stores discussions related to patches

Each table uses:
- Environment-specific table names
- Primary keys optimized for common access patterns
- Global Secondary Indexes (GSIs) for efficient queries
- PAY_PER_REQUEST billing for dev/staging, PROVISIONED for production
- Point-in-time recovery enabled
- Time-to-live (TTL) attribute configured

### EventBridge

EventBridge provides the scheduling and event management:

- **Hourly Rule**: Fetches recent patches every hour
- **Daily Rule**: Performs a full refresh at 3 AM UTC
- **Weekly Rule**: Refreshes discussions for recent patches on Sundays

EventBridge configuration includes:
- Dead letter queues for failed invocations
- Retry policies with exponential backoff
- CloudWatch alarms for monitoring failures

### Other Services

- **SQS**: Dead letter queues for failed function executions
- **CloudWatch**: Monitoring, logging, and alerting
- **IAM**: Secure permission management
- **API Gateway** (Planned): RESTful API interface

## Code Organization

The backend code is organized into several layers:

### Functions Layer

Lambda function handlers with minimal business logic:

```
src/
  functions/
    fetch-patches/
      index.py
      requirements.txt
    fetch-discussions/
      index.py
      requirements.txt
    refresh-discussions/
      index.py
      requirements.txt
```

### Models Layer

Data models and type definitions:

```
src/
  models/
    types.ts           # Domain models
    api-types.ts       # API response types
    database.ts        # Database models
```

### Repositories Layer

Data access logic using the repository pattern:

```
src/
  repositories/
    patch_repository.py
    discussion_repository.py
```

### Utilities Layer

Common utility functions:

```
src/
  utils/
    api.py             # API interaction utilities
    dynamodb.py        # DynamoDB utilities
    metrics.py         # CloudWatch metrics utilities
    patchwork_api.py   # Patchwork API client
```

## Backend Processing Flow

1. **Scheduled Execution**:
   - EventBridge rules trigger Lambda functions at scheduled intervals

2. **Data Fetching**:
   - Lambda functions fetch data from external sources
   - Data is transformed to match internal data models

3. **Data Storage**:
   - Repository layer handles data persistence
   - DynamoDB operations are encapsulated in repositories

4. **Error Handling**:
   - Exceptions are caught and logged
   - Retry mechanisms are implemented for transient failures
   - Failed executions are sent to dead letter queues

5. **Metrics and Monitoring**:
   - Custom metrics are published to CloudWatch
   - Lambda execution metrics are tracked
   - API call metrics are recorded

## Security

The backend implements several security measures:

- **IAM Roles**: Least privilege principle for Lambda functions
- **Environment Isolation**: Separate resources for each environment
- **Secure Configuration**: Environment variables for sensitive settings
- **Input Validation**: Validation of all external inputs
- **Error Handling**: Proper error handling without leaking sensitive information

## Deployment

The backend is deployed using AWS CDK:

- **Infrastructure as Code**: All resources defined in TypeScript
- **Environment Configuration**: Environment-specific settings
- **CI/CD Integration**: GitHub Actions for automated deployment
- **Resource Protection**: Deletion protection for production resources