# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

For detailed architecture documentation, see [Architecture Documentation](./docs/architecture/).

- **Backend**: AWS CDK (TypeScript), Python 3.9 Lambda functions, DynamoDB, EventBridge
- **Data Flow**:
  1. Lambda functions fetch data from Patchwork API and lore.kernel.org
  2. Data is processed, correlated, and stored in DynamoDB
  3. EventBridge schedules regular data fetching and processing

### Core Architecture Components

- [Architecture Overview](./docs/architecture/overview.md): System diagrams and high-level design
- [Backend Architecture](./docs/architecture/backend.md): Detailed AWS services and code organization
- [Data Models](./docs/architecture/data-models.md): Domain and database models
- [Design Patterns](./docs/architecture/design-patterns.md): Key patterns used in the application

### Key Architectural Principles

1. **Serverless First**: Utilizing AWS managed services to minimize operational overhead
2. **Event-Driven Design**: Using events for loose coupling between components
3. **Repository Pattern**: Abstracting data access through clean interfaces
4. **Single-Table Design**: Optimizing DynamoDB access patterns
5. **Infrastructure as Code**: All infrastructure defined through AWS CDK
6. **Comprehensive Error Handling**: Using retry mechanisms and dead letter queues

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