# Demo 6: Multi-Environment Support

This demo shows how LKML Assistant supports multiple deployment environments with environment-specific configurations.

## Prerequisites

- AWS CLI installed and configured with access to the deployment account
- Deployed LKML Assistant application (at least in the dev environment)

## Demo Steps

### 1. Examine Environment Variables

```bash
# Get the Lambda function configuration and view environment variables
aws lambda get-function-configuration \
  --function-name LkmlAssistant-FetchPatches-dev \
  --query "Environment.Variables"
```

### 2. Compare Environment Settings in CDK

```bash
# View the infrastructure code with environment differences
cat <<'EOF' | grep -A5 -B5 "this.isProd"
import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';

// ... 

// Define DynamoDB tables with environment-specific settings
this.patchesTable = new dynamodb.Table(this, 'PatchesTable', {
  tableName: `LkmlAssistant-${this.environmentName}-Patches`,
  partitionKey: { name: 'id', type: dynamodb.AttributeType.STRING },
  billingMode: this.isProd ? dynamodb.BillingMode.PROVISIONED : dynamodb.BillingMode.PAY_PER_REQUEST,
  readCapacity: this.isProd ? 5 : undefined,
  writeCapacity: this.isProd ? 5 : undefined,
  removalPolicy: this.isProd ? cdk.RemovalPolicy.RETAIN : cdk.RemovalPolicy.DESTROY,
  pointInTimeRecovery: true,
});

// ...

// Common Lambda configuration
const commonLambdaProps = {
  runtime: lambda.Runtime.PYTHON_3_9,
  memorySize: this.isProd ? 1024 : 512,
  tracing: this.isProd ? lambda.Tracing.ACTIVE : lambda.Tracing.DISABLED,
  logRetention: this.isProd ? 
    logs.RetentionDays.ONE_MONTH : 
    logs.RetentionDays.ONE_WEEK,
};
EOF
```

### 3. View Environment Deployment Script

```bash
# View the deployment script with environment handling
cat <<'EOF' | grep -A5 -B5 "ENV="
#!/bin/bash

# Get the environment name from the ENV variable, default to dev
ENV=${ENV:-dev}
echo "Deploying to $ENV environment"

# Validate environment
if [[ "$ENV" != "dev" && "$ENV" != "staging" && "$ENV" != "prod" ]]; then
  echo "Error: ENV must be one of: dev, staging, prod"
  exit 1
fi

# Handle prod deployments with extra care
if [[ "$ENV" == "prod" && -z "$CONFIRM_PROD" ]]; then
  echo "⚠️ You are attempting to deploy to PRODUCTION ⚠️"
  echo "This will affect live users and data."
  echo "To confirm, run with: CONFIRM_PROD=yes ENV=prod ./scripts/deploy.sh"
  exit 1
fi
EOF
```

### 4. Check Environment-Specific Resource Names

```bash
# List all Lambda functions to see environment naming
aws lambda list-functions \
  --query "Functions[?starts_with(FunctionName, 'LkmlAssistant')].FunctionName" \
  --output table

# List all DynamoDB tables to see environment naming
aws dynamodb list-tables \
  --query "TableNames[?contains(@, 'LkmlAssistant')]" \
  --output table

# List all CloudWatch dashboards to see environment naming
aws cloudwatch list-dashboards \
  --dashboard-name-prefix LkmlAssistant \
  --query "DashboardEntries[].DashboardName" \
  --output table
```

### 5. Compare AWS Resource Configurations Across Environments

```bash
# If multiple environments are deployed, compare their settings
# For example, compare DynamoDB table configurations

# Get dev table settings
aws dynamodb describe-table \
  --table-name LkmlAssistant-Patches-dev \
  --query "Table.{Name:TableName,BillingMode:BillingModeSummary.BillingMode,DeletionProtection:DeletionProtectionEnabled}"

# If there's a prod deployment, compare settings
if aws dynamodb describe-table --table-name LkmlAssistant-Patches-prod 2>/dev/null; then
  aws dynamodb describe-table \
    --table-name LkmlAssistant-Patches-prod \
    --query "Table.{Name:TableName,BillingMode:BillingModeSummary.BillingMode,DeletionProtection:DeletionProtectionEnabled}"
fi
```

### 6. Check CloudFormation Stack Configuration

```bash
# View the deployed stack parameters with environment name
aws cloudformation describe-stacks \
  --stack-name LkmlAssistantStack-dev \
  --query "Stacks[0].Parameters[?ParameterKey=='environmentName']"
```

## Expected Results

- You should see environment-specific settings in Lambda functions, including:
  - Environment variables with "dev", "staging", or "prod" values
  - Different memory allocations based on environment
- Resource names should include the environment name (e.g., "LkmlAssistant-Patches-dev")
- DynamoDB tables in production should use provisioned capacity, while dev uses on-demand
- Production resources should have deletion protection enabled
- CloudWatch retention should be longer in production than in development
- X-Ray tracing should be enabled in production but disabled in development

## Key Features Demonstrated

- Environment-based resource isolation
- Environment-specific configuration
- Progressive resource configurations (more resources in prod)
- Resource naming conventions
- Deployment safeguards for production
- Cost optimization for different environments