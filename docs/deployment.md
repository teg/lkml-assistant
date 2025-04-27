# Deployment Guide

This document provides information about the deployment process for the LKML Assistant application.

## Environments

The application supports three environments:

- **dev**: Development environment for day-to-day development work
- **staging**: Pre-production environment for testing before release
- **prod**: Production environment

## Deployment Pipeline

The project uses GitHub Actions for continuous integration and deployment:

1. **CI Workflow** (`ci.yml`):
   - Runs automatically on push to main and pull requests
   - Performs lint checks, unit tests, and builds the CDK app
   - Ensures code quality and prevents broken code from being merged

2. **Deployment Workflow** (`deploy.yml`):
   - Automatic deployment to dev environment on successful CI run
   - Manual deployment to staging and production environments
   - Implements promotion model: dev → staging → production

## Manual Deployment

You can also deploy manually using the deployment script:

```bash
# Deploy to dev environment (default)
./scripts/deploy.sh

# Deploy to staging environment
ENV=staging ./scripts/deploy.sh

# Deploy to production environment (requires confirmation)
ENV=prod ./scripts/deploy.sh
```

## AWS Permissions

To deploy this application, you need AWS credentials with the following permissions:

- IAM role creation and management
- DynamoDB table creation and management
- Lambda function creation and management
- EventBridge rule creation and management
- CloudWatch logs, metrics, and alarms creation
- SQS queue creation and management

For GitHub Actions, create AWS access keys and store them as GitHub repository secrets:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`

## Infrastructure as Code

The infrastructure is defined using AWS CDK in TypeScript. Key files:

- `infra/bin/lkml-assistant.ts`: CDK app entry point
- `infra/lib/lkml-assistant-stack.ts`: Main stack definition

## Environment-specific Configuration

The deployment uses environment-specific settings:

1. **Development**:
   - Pay-per-request DynamoDB billing
   - Lower Lambda memory allocations
   - Shorter log retention
   - Relaxed security permissions
   - Resources can be deleted

2. **Production**:
   - Provisioned DynamoDB capacity
   - Higher Lambda memory allocations
   - Longer log retention
   - Stricter security permissions
   - Resources protected from deletion
   - X-Ray tracing enabled

## Rollback Process

To roll back a deployment:

1. For automatic rollback, use the AWS CloudFormation console to roll back to a previous deployment
2. For manual rollback, deploy a previous version using the `git checkout` command followed by the deployment script

## Monitoring

The deployment includes:

- CloudWatch dashboards for each environment
- Alarms for critical metrics
- Dead Letter Queue (DLQ) monitoring
- Custom metrics for tracking application performance

## Security Considerations

- Production uses more restrictive IAM permissions
- Resources in production are protected from accidental deletion
- Environment-specific resource naming prevents cross-environment access