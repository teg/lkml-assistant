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

### IAM Policy for Deployment

Create a user with the following IAM policy that provides scoped access to manage LKML Assistant resources while limiting exposure to other AWS resources:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "cloudformation:ListExports",
                "cloudwatch:PutMetricData",
                "logs:DeleteIntegration",
                "cloudformation:DeactivateType",
                "cloudwatch:CreateServiceLevelObjective",
                "logs:ListLogDeliveries",
                "cloudformation:ListTypeRegistrations",
                "cloudwatch:ListServices",
                "cloudformation:BatchDescribeTypeConfigurations",
                "lambda:ListLayers",
                "dynamodb:ListImports",
                "lambda:ListCodeSigningConfigs",
                "logs:PutIndexPolicy",
                "logs:DescribeDestinations",
                "cloudwatch:DescribeInsightRules",
                "lambda:ListFunctions",
                "events:ListConnections",
                "logs:GetIntegration",
                "logs:DeleteQueryDefinition",
                "cloudwatch:GetMetricStatistics",
                "logs:PutIntegration",
                "events:TestEventPattern",
                "cloudformation:ListGeneratedTemplates",
                "cloudformation:GetGeneratedTemplate",
                "logs:ListLogGroupsForQuery",
                "cloudformation:ActivateOrganizationsAccess",
                "dynamodb:DescribeReservedCapacity",
                "events:RemovePermission",
                "logs:DescribeDeliveries",
                "cloudformation:TestType",
                "cloudformation:ValidateTemplate",
                "cloudformation:RegisterType",
                "cloudformation:CreateUploadBucket",
                "cloudformation:SetTypeDefaultVersion",
                "cloudformation:DescribeOrganizationsAccess",
                "dynamodb:ListTables",
                "logs:DescribeIndexPolicies",
                "dynamodb:GetAbacStatus",
                "cloudformation:SetTypeConfiguration",
                "cloudwatch:ListMetrics",
                "cloudformation:ListResourceScanResources",
                "cloudformation:EstimateTemplateCost",
                "dynamodb:DescribeReservedCapacityOfferings",
                "cloudformation:StartResourceScan",
                "logs:StopLiveTail",
                "logs:DeleteLogDelivery",
                "dynamodb:DescribeLimits",
                "cloudwatch:GetMetricWidgetImage",
                "cloudwatch:BatchGetServiceLevelIndicatorReport",
                "cloudformation:DescribeType",
                "events:ListReplays",
                "cloudformation:ListImports",
                "logs:ListLogGroupsForEntity",
                "s3:*",
                "cloudformation:PublishType",
                "cloudwatch:EnableTopologyDiscovery",
                "logs:ListIntegrations",
                "logs:DescribeAccountPolicies",
                "logs:TestMetricFilter",
                "logs:PutAccountPolicy",
                "events:ListEventBuses",
                "cloudwatch:Link",
                "cloudformation:DescribeTypeRegistration",
                "cloudwatch:ListManagedInsightRules",
                "dynamodb:ListStreams",
                "events:ListArchives",
                "dynamodb:ListContributorInsights",
                "dynamodb:ListGlobalTables",
                "cloudformation:UpdateGeneratedTemplate",
                "logs:DescribeConfigurationTemplates",
                "logs:TestTransformer",
                "cloudwatch:ListMetricStreams",
                "logs:DeleteIndexPolicy",
                "cloudformation:ListResourceScanRelatedResources",
                "cloudformation:ActivateType",
                "events:ListEndpoints",
                "events:ListRuleNamesByTarget",
                "events:ListPartnerEventSources",
                "cloudwatch:DescribeAlarmsForMetric",
                "logs:CancelExportTask",
                "cloudwatch:ListDashboards",
                "events:ListRules",
                "cloudwatch:ListEntitiesForMetric",
                "lambda:ListLayerVersions",
                "cloudformation:DeleteGeneratedTemplate",
                "cloudwatch:PutAnomalyDetector",
                "cloudformation:CreateStackSet",
                "cloudwatch:PutManagedInsightRules",
                "cloudformation:DeactivateOrganizationsAccess",
                "dynamodb:UpdateAbacStatus",
                "logs:DescribeDeliverySources",
                "logs:StopQuery",
                "cloudwatch:GetTopologyDiscoveryStatus",
                "logs:Link",
                "logs:CreateLogDelivery",
                "cloudformation:CreateGeneratedTemplate",
                "logs:PutResourcePolicy",
                "logs:DescribeExportTasks",
                "logs:UpdateLogDelivery",
                "lambda:ListEventSourceMappings",
                "cloudformation:DescribeGeneratedTemplate",
                "dynamodb:DescribeEndpoints",
                "logs:ListEntitiesForLogGroup",
                "cloudformation:ListTypeVersions",
                "cloudformation:DescribeStackDriftDetectionStatus",
                "cloudwatch:GenerateQuery",
                "cloudformation:RegisterPublisher",
                "cloudwatch:GetMetricData",
                "cloudformation:ListTypes",
                "dynamodb:PurchaseReservedCapacityOfferings",
                "lambda:GetAccountSettings",
                "lambda:CreateEventSourceMapping",
                "logs:GetLogDelivery",
                "cloudwatch:GetTopologyMap",
                "cloudwatch:DeleteAnomalyDetector",
                "cloudformation:DeregisterType",
                "cloudwatch:DescribeAnomalyDetectors",
                "logs:DeleteAccountPolicy",
                "logs:DeleteResourcePolicy",
                "events:PutPartnerEvents",
                "events:ListEventSources",
                "cloudformation:DescribeAccountLimits",
                "logs:DescribeQueryDefinitions",
                "dynamodb:ListExports",
                "logs:DescribeResourcePolicies",
                "lambda:CreateCodeSigningConfig",
                "logs:DescribeQueries",
                "cloudformation:ListResourceScans",
                "sqs:ListQueues",
                "cloudformation:ListStacks",
                "events:ListApiDestinations",
                "logs:DescribeLogGroups",
                "dynamodb:ListBackups",
                "logs:PutQueryDefinition",
                "cloudformation:DescribePublisher",
                "logs:DescribeFieldIndexes",
                "events:PutPermission",
                "logs:DescribeDeliveryDestinations",
                "cloudwatch:ListServiceLevelObjectives",
                "cloudformation:ListStackSets",
                "cloudformation:DescribeResourceScan"
            ],
            "Resource": "*"
        },
        {
            "Sid": "VisualEditor1",
            "Effect": "Allow",
            "Action": [
                "iam:PassRole",
                "cloudwatch:*",
                "logs:*",
                "lambda:*",
                "cloudformation:*",
                "dynamodb:*",
                "sqs:*",
                "events:*"
            ],
            "Resource": [
                "arn:aws:lambda:*:*:function:LkmlAssistant-*",
                "arn:aws:iam::*:role/LkmlAssistant-*",
                "arn:aws:sqs:*:*:LkmlAssistant-*",
                "arn:aws:events:*:*:rule/LkmlAssistant-*",
                "arn:aws:cloudformation:*:*:stack/LkmlAssistant*/*",
                "arn:aws:logs:*:*:log-group:LkmlAssistant-*",
                "arn:aws:cloudwatch::*:dashboard/LkmlAssistant-*",
                "arn:aws:dynamodb:*:*:table/LkmlAssistant-*"
            ]
        }
    ]
}
```

This policy provides:

1. Limited read permissions on global AWS resources (first statement)
2. Full permissions but only for resources with the "LkmlAssistant-" prefix (second statement)
3. Full S3 access (needed for CloudFormation template deployment)

This policy achieves isolation by limiting full permissions only to the resources that belong to this application.

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