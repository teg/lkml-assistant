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

## Implementation Phases

### Phase 1: Backend Infrastructure
1. **Project Setup**
   - Initialize AWS CDK project with TypeScript
   - Set up project structure and directories
   - Configure AWS credentials and profiles

2. **Define Core Data Models**
   - Define DynamoDB table schemas:
     - Patches Table (metadata about patches)
     - Discussions Table (discussions related to patches)
   - Create TypeScript interfaces for data models

3. **Data Fetching Layer**
   - Create Lambda function to fetch patches from Patchwork API
     - Endpoint: https://patchwork.kernel.org/api/1.1/projects/rust-for-linux/patches/
     - Handle pagination and API limits
   - Create Lambda function to fetch discussions from lore.kernel.org
     - Parse email threads and conversations

4. **Data Storage Implementation**
   - Implement DynamoDB table creation and configuration
   - Set up partition keys and sort keys for efficient querying
   - Create base CRUD operations for data access

5. **Scheduling**
   - Set up EventBridge rules for scheduled execution
     - Configure hourly triggers for patch fetching
   - Implement error handling and retry mechanisms

6. **Deployment Pipeline**
   - Create CDK deployment stack
   - Configure environment variables and secrets management
   - Implement logging and monitoring

7. **Testing**
   - Write unit tests for Lambda functions
   - Create integration tests for API interactions
   - Test DynamoDB access patterns

### Phase 2: Data Processing
- Implement patch status tracking
- Add discussion threading
- Create summarization logic

### Phase 3: Frontend
- Set up Amplify hosting
- Build React components
- Implement authentication
- Create dashboard views

### Phase 4: Integration & Deployment
- Connect frontend to backend
- Set up CI/CD pipeline
- Deploy to production