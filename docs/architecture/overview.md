# Architecture Overview

This document provides a high-level overview of the LKML Assistant architecture.

## System Architecture Diagram

```
┌───────────────────┐     ┌──────────────────┐     ┌───────────────────┐
│                   │     │                  │     │                   │
│  External Sources │────▶│ AWS Lambda       │────▶│ DynamoDB          │
│  - Patchwork API  │     │ - Fetch Patches  │     │ - Patches Table   │
│  - lore.kernel.org│     │ - Fetch Discussions    │ - Discussions Table│
│                   │     │                  │     │                   │
└───────────────────┘     └──────────────────┘     └───────────────────┘
                                    │                        │
                                    ▼                        │
                          ┌──────────────────┐               │
                          │                  │               │
                          │ EventBridge      │               │
                          │ - Schedulers     │               │
                          │ - Event Rules    │               │
                          │                  │               │
                          └──────────────────┘               │
                                    │                        │
                                    ▼                        ▼
┌───────────────────┐     ┌──────────────────┐     ┌───────────────────┐
│                   │     │                  │     │                   │
│  Frontend         │◀───▶│ API Gateway     │◀───▶│ Lambda Functions  │
│  - React.js       │     │ - RESTful API   │     │ - Data Access     │
│  - Amplify        │     │ - GraphQL       │     │ - Processing      │
│                   │     │                  │     │                   │
└───────────────────┘     └──────────────────┘     └───────────────────┘
```

## Core Components

### Data Sources

- **Patchwork API**: Source for patch information from the Rust for Linux project
- **lore.kernel.org**: Source for discussion threads and email conversations

### Backend Components

- **AWS Lambda**: Serverless functions for data fetching, processing, and API handling
- **DynamoDB**: NoSQL database for storing patch and discussion data
- **EventBridge**: Event bus for scheduling and event-driven processing
- **API Gateway**: RESTful API and GraphQL interface for frontend access

### Frontend Components (Planned)

- **React.js**: JavaScript library for building the user interface
- **AWS Amplify**: Hosting, authentication, and API integration

## Data Flow

1. **Data Collection**:
   - Lambda functions fetch data from Patchwork API and lore.kernel.org on scheduled intervals
   - Raw data is transformed into the application's data model

2. **Data Storage**:
   - Processed data is stored in DynamoDB tables
   - Global Secondary Indexes enable efficient querying

3. **Data Processing**:
   - Additional Lambda functions process the stored data
   - Operations include threading discussions, tracking status changes, and generating summaries

4. **Data Access**:
   - Frontend requests data through API Gateway
   - Lambda functions retrieve and return the requested data from DynamoDB

## Deployment Environments

The architecture supports multiple deployment environments:

- **Development**: For day-to-day development work
- **Staging**: For pre-production testing
- **Production**: For end-user access

Each environment has its own isolated set of resources.

## Key Architectural Decisions

1. **Serverless Architecture**:
   - Lower operational overhead
   - Automatic scaling
   - Pay-per-use cost model

2. **Event-Driven Processing**:
   - Decoupling of components
   - Asynchronous processing
   - Better resilience to failures

3. **AWS CDK for Infrastructure**:
   - Infrastructure as code
   - TypeScript for type safety
   - Simplified deployment and updates

4. **Repository Pattern**:
   - Separation of data access from business logic
   - Improved testability
   - Consistent data access patterns

For more detailed information on specific components, refer to the other architecture documentation files.