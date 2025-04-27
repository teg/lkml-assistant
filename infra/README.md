# LKML Assistant Infrastructure

This directory contains the AWS CDK infrastructure code for the LKML Assistant application.

## Directory Structure

- `bin/`: CDK app entry point
- `lib/`: CDK constructs and stacks
- `test/`: CDK infrastructure tests

## Getting Started

1. Install dependencies:

```bash
npm install
```

2. Build the TypeScript code:

```bash
npm run build
```

3. Deploy the stack:

```bash
# Deploy to development environment
npm run deploy:dev

# Deploy to staging environment
npm run deploy:staging

# Deploy to production environment
npm run deploy:prod
```

## Environment Configuration

The infrastructure is designed to support multiple environments:

- **dev**: Development environment (default)
- **staging**: Pre-production environment
- **prod**: Production environment

Each environment has its own configuration settings defined in the stack.

## Available Commands

- `npm run build`: Compile TypeScript code
- `npm run watch`: Watch for changes and compile
- `npm run test`: Run tests
- `npm run lint`: Lint TypeScript code
- `npm run format`: Format TypeScript code
- `npm run cdk`: Run CDK commands
- `npm run bootstrap`: Bootstrap CDK environment
- `npm run synth`: Synthesize CloudFormation template
- `npm run diff`: Compare deployed stack with current code
- `npm run deploy`: Deploy stack
- `npm run deploy:dev`: Deploy to dev environment
- `npm run deploy:staging`: Deploy to staging environment
- `npm run deploy:prod`: Deploy to production environment
- `npm run destroy:dev`: Destroy dev environment
- `npm run destroy:staging`: Destroy staging environment

## Resources Created

This stack creates the following AWS resources:

- DynamoDB tables for storing patch and discussion data
- Lambda functions for fetching and processing data
- EventBridge rules for scheduled execution
- SQS queues for error handling
- CloudWatch alarms and dashboards for monitoring
- IAM roles and policies for security

## Dashboard

The stack creates a CloudWatch dashboard for monitoring the application. After deployment, you can access the dashboard URL from the CloudFormation outputs.

## Local Development

For local development and testing, you can use the Docker Compose setup in the root directory:

```bash
docker-compose up -d
```

This provides:
- Local DynamoDB
- LocalStack for emulating AWS services
- DynamoDB Admin UI

## Troubleshooting

- If deployment fails, check the CloudFormation events in the AWS console for details
- For Lambda function errors, check CloudWatch Logs
- For deployment issues, make sure your AWS credentials are valid and have the necessary permissions