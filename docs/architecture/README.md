# Architecture Documentation

This directory contains comprehensive documentation on the architecture of the LKML Assistant project.

## Contents

- [Overview](./overview.md): High-level architecture overview
- [Backend Architecture](./backend.md): Detailed backend design
- [Data Models](./data-models.md): Data schemas and relationships
- [Design Patterns](./design-patterns.md): Key design patterns used

## System Architecture

The LKML Assistant uses a serverless, event-driven architecture built on AWS. The system is designed to be scalable, resilient, and cost-effective, with clear separation of concerns between components.

### Technology Stack

- **Infrastructure as Code**: AWS CDK with TypeScript
- **Backend**: AWS Lambda, DynamoDB, EventBridge
- **API Layer**: API Gateway (planned for Phase 2)
- **CI/CD**: GitHub Actions

### Key Architectural Principles

1. **Serverless First**: Utilizing fully managed services to minimize operational overhead
2. **Event-Driven Design**: Using events for loose coupling between components
3. **Single Responsibility**: Each Lambda function has a focused purpose
4. **Repository Pattern**: Abstracting data access through clean interfaces
5. **Infrastructure as Code**: All infrastructure defined and versioned with AWS CDK
6. **Single-Table Design**: Optimizing DynamoDB access patterns
7. **Comprehensive Error Handling**: Using retry mechanisms and dead letter queues
8. **Multi-Environment Support**: Separate development, staging, and production environments

### System Boundaries

LKML Assistant interacts with external systems including:

- **Patchwork API**: For retrieving patch metadata
- **lore.kernel.org**: For accessing full patch content and discussions
- **Email delivery services**: For sending notifications (planned)
- **CloudWatch**: For monitoring and logging

### Architecture Decision Records

The project maintains [Architecture Decision Records (ADRs)](./decisions/) to document the significant architectural decisions made during development.