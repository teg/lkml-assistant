# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
This project monitors the Rust for Linux mailing list, tracks patches/PRs, and provides summaries of discussions and patch statuses. It uses a serverless architecture on AWS.

## Build/Lint/Test Commands
- Build: `make build`
- Lint: `make lint`
- Test (all): `make test`
- Test (single): `make test TEST=test_name.py`
- Format code: `make fmt`

## Code Style Guidelines
- Follow Linux kernel coding style for C/C++ code
- PEP 8 for Python code
- TypeScript standard guidelines for CDK code
- Use type annotations in Python and TypeScript
- Use 4 spaces for indentation (no tabs)
- Maximum line length: 100 characters
- Import order: standard library, third-party, local
- Function/method names: snake_case
- Class names: CamelCase
- Constants: UPPERCASE_WITH_UNDERSCORES
- Error handling: prefer early returns, use appropriate error codes
- Include descriptive docstrings for all functions and classes
- Keep functions focused on a single responsibility
- Write unit tests for all new functionality

## Project Organization
- Source code in `src/` directory
- Tests in `tests/` directory
- Documentation in `docs/` directory
- Infrastructure as code in `infra/` directory

## Architecture
- **Backend**: AWS CDK (TypeScript), Python 3.9 Lambda functions, DynamoDB, EventBridge
- **Frontend**: React.js, AWS Amplify for hosting and CI/CD
- **Data Flow**:
  1. Lambda functions fetch data from Patchwork API and lore.kernel.org
  2. Data is processed, correlated, and summarized
  3. Frontend accesses data through Amplify API and API Gateway

## Design Patterns & Architectural Decisions

### Repository Pattern
- Separation of data access logic from business logic
- Abstraction layer (repositories) between domain models and data access
- Repository interfaces provide clear API for data operations
- Benefits:
  - Improved testability through mocking
  - Consistent data access and error handling
  - Flexibility to change database implementation
  - Centralized query logic

### Single-Table Design (DynamoDB)
- All patch data in one table, all discussion data in another
- Uses composite keys and global secondary indexes (GSIs) for access patterns
- Key design:
  - Primary keys for direct access
  - GSIs with composite keys for querying relationships
  - Convention-based keys (e.g., `TYPE#id`) for consistent patterns

### Event-Driven Architecture
- EventBridge for scheduled triggers
- Lambda-to-Lambda chaining for data processing
- Asynchronous data processing pipeline

### Error Handling & Resilience
- Retry mechanism with exponential backoff
- Consistent error handling pattern using decorators
- Detailed logging for troubleshooting

## Implementation Roadmap

The implementation is divided into four major phases. For detailed information about each phase, please refer to the [Implementation Documentation](./docs/implementation/).

### Phase 1: Backend Infrastructure (✅ Completed)
- Project setup and AWS CDK configuration
- Data model and schema definition
- Data fetching from external sources
- Data storage and access patterns
- Scheduled processing with EventBridge
- Deployment pipeline and environments
- Testing and quality assurance

### Phase 2: Data Processing (🔄 Planned)
- Patch status tracking and updates
- Discussion threading and correlation
- Content summarization with NLP
- Advanced event processing
- Notification system

### Phase 3: Frontend (🔄 Planned)
- AWS Amplify setup and configuration
- React application architecture
- User authentication and authorization
- Dashboard views and components
- Data visualization

### Phase 4: Integration & Deployment (🔄 Planned)
- API Gateway configuration
- Frontend-backend integration
- Comprehensive CI/CD pipeline
- Security hardening
- Production deployment
- Monitoring and alerting

For detailed implementation information, see the [full implementation docs](./docs/implementation/).