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
1. Backend Infrastructure (CDK, DynamoDB, Lambda, EventBridge)
2. Data Processing (patch tracking, discussion threading, summarization)
3. Frontend (Amplify, React components, authentication, dashboard)
4. Integration & Deployment (API connections, CI/CD pipeline, production)