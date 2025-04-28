import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as path from 'path';
import { createDashboard } from './dashboard';

export interface LkmlAssistantStackProps extends cdk.StackProps {
  environmentName?: string;
}

export class LkmlAssistantStack extends cdk.Stack {
  // Make tables public so they can be accessed by other constructs
  public readonly patchesTable: dynamodb.Table;
  public readonly discussionsTable: dynamodb.Table;
  public readonly fetchPatchesLambda: lambda.Function;
  public readonly fetchDiscussionsLambda: lambda.Function;
  
  // Environment configuration
  readonly environmentName: string;
  private readonly isProd: boolean;

  constructor(scope: Construct, id: string, props?: LkmlAssistantStackProps) {
    // Make sure we have a valid AWS env for tests
    const stackProps: cdk.StackProps = {
      ...props,
      env: props?.env || { account: '123456789012', region: 'us-east-1' }
    };
    
    super(scope, id, stackProps);
    
    // Set environment (default to dev)
    this.environmentName = props?.environmentName || 'dev';
    this.isProd = this.environmentName === 'prod';
    
    // Add environment tag to all resources
    cdk.Tags.of(this).add('Environment', this.environmentName);
    cdk.Tags.of(this).add('Project', 'LkmlAssistant');

    // Define DynamoDB tables with environment-specific settings
    this.patchesTable = new dynamodb.Table(this, 'PatchesTable', {
      tableName: `LkmlAssistant-Patches-${this.environmentName}`,
      partitionKey: { name: 'id', type: dynamodb.AttributeType.STRING },
      billingMode: this.isProd ? dynamodb.BillingMode.PROVISIONED : dynamodb.BillingMode.PAY_PER_REQUEST,
      readCapacity: this.isProd ? 5 : undefined,
      writeCapacity: this.isProd ? 5 : undefined,
      removalPolicy: this.isProd ? cdk.RemovalPolicy.RETAIN : cdk.RemovalPolicy.DESTROY,
      pointInTimeRecovery: true,
      timeToLiveAttribute: 'ttl',
    });

    // Add GSIs for Patches table
    this.patchesTable.addGlobalSecondaryIndex({
      indexName: 'SubmitterIndex',
      partitionKey: { name: 'gsi1pk', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'gsi1sk', type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    this.patchesTable.addGlobalSecondaryIndex({
      indexName: 'SeriesIndex',
      partitionKey: { name: 'gsi2pk', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'gsi2sk', type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    this.patchesTable.addGlobalSecondaryIndex({
      indexName: 'StatusIndex',
      partitionKey: { name: 'gsi3pk', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'gsi3sk', type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    this.discussionsTable = new dynamodb.Table(this, 'DiscussionsTable', {
      tableName: `LkmlAssistant-Discussions-${this.environmentName}`,
      partitionKey: { name: 'id', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'timestamp', type: dynamodb.AttributeType.STRING },
      billingMode: this.isProd ? dynamodb.BillingMode.PROVISIONED : dynamodb.BillingMode.PAY_PER_REQUEST,
      readCapacity: this.isProd ? 5 : undefined,
      writeCapacity: this.isProd ? 5 : undefined,
      removalPolicy: this.isProd ? cdk.RemovalPolicy.RETAIN : cdk.RemovalPolicy.DESTROY,
      pointInTimeRecovery: true,
      timeToLiveAttribute: 'ttl',
    });

    // Add GSIs for Discussions table
    this.discussionsTable.addGlobalSecondaryIndex({
      indexName: 'PatchIndex',
      partitionKey: { name: 'gsi1pk', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'gsi1sk', type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    this.discussionsTable.addGlobalSecondaryIndex({
      indexName: 'ThreadIndex',
      partitionKey: { name: 'gsi2pk', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'gsi2sk', type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    this.discussionsTable.addGlobalSecondaryIndex({
      indexName: 'AuthorIndex',
      partitionKey: { name: 'gsi3pk', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'gsi3sk', type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // Define Lambda functions
    
    // Common Lambda configuration
    const commonLambdaProps = {
      runtime: lambda.Runtime.PYTHON_3_9,
      memorySize: this.isProd ? 1024 : 512,
      tracing: this.isProd ? lambda.Tracing.ACTIVE : lambda.Tracing.DISABLED,
      logRetention: this.isProd ? 
        logs.RetentionDays.ONE_MONTH : 
        logs.RetentionDays.ONE_WEEK,
    };
    
    // Environment variables for metrics
    const commonEnvVars = {
      ENVIRONMENT: this.environmentName,
      METRIC_SOURCE: 'lambda',
      LOG_LEVEL: this.isProd ? 'INFO' : 'DEBUG',
    };
    
    // 1. Fetch Patches Lambda
    this.fetchPatchesLambda = new lambda.Function(this, 'FetchPatchesFunction', {
      ...commonLambdaProps,
      functionName: `LkmlAssistant-FetchPatches-${this.environmentName}`,
      handler: 'src/functions/fetch-patches/index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../'), {
        exclude: [
          'infra/**', 
          'node_modules/**', 
          '.git/**',
          'docs/**',
          '.pytest_cache/**',
          'htmlcov/**',
          '**/__pycache__/**',
          '**/*.pyc'
        ]
      }),
      timeout: cdk.Duration.seconds(300),
      environment: {
        ...commonEnvVars,
        PATCHES_TABLE_NAME: this.patchesTable.tableName,
        FETCH_DISCUSSIONS_LAMBDA: `LkmlAssistant-FetchDiscussions-${this.environmentName}`,
      },
    });
    
    // Grant DynamoDB permissions to FetchPatches Lambda
    this.patchesTable.grantWriteData(this.fetchPatchesLambda);
    
    // Grant Lambda permissions to invoke other Lambdas - restrict to same environment
    if (this.isProd) {
      // In production, restrict to specific ARNs
      this.fetchPatchesLambda.addToRolePolicy(new iam.PolicyStatement({
        actions: ['lambda:InvokeFunction'],
        resources: [`arn:aws:lambda:${this.region}:${this.account}:function:LkmlAssistant-*-${this.environmentName}`],
      }));
    } else {
      // In dev/staging, less restrictive
      this.fetchPatchesLambda.addToRolePolicy(new iam.PolicyStatement({
        actions: ['lambda:InvokeFunction'],
        resources: ['*'],
        conditions: {
          'StringLike': {
            'lambda:FunctionName': `LkmlAssistant-*-${this.environmentName}`
          }
        }
      }));
    }
    
    // Add CloudWatch permissions for metrics
    this.fetchPatchesLambda.addToRolePolicy(new iam.PolicyStatement({
      actions: ['cloudwatch:PutMetricData'],
      resources: ['*'],
      conditions: {
        'StringEquals': {
          'cloudwatch:namespace': 'LkmlAssistant'
        }
      }
    }));
    
    // 2. Fetch Discussions Lambda
    this.fetchDiscussionsLambda = new lambda.Function(this, 'FetchDiscussionsFunction', {
      ...commonLambdaProps,
      functionName: `LkmlAssistant-FetchDiscussions-${this.environmentName}`,
      handler: 'src/functions/fetch-discussions/index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../'), {
        exclude: [
          'infra/**', 
          'node_modules/**', 
          '.git/**',
          'docs/**',
          '.pytest_cache/**',
          'htmlcov/**',
          '**/__pycache__/**',
          '**/*.pyc'
        ]
      }),
      timeout: cdk.Duration.seconds(300),
      environment: {
        ...commonEnvVars,
        DISCUSSIONS_TABLE_NAME: this.discussionsTable.tableName,
        PATCHES_TABLE_NAME: this.patchesTable.tableName,
      },
    });
    
    // Grant DynamoDB permissions to FetchDiscussions Lambda
    this.discussionsTable.grantWriteData(this.fetchDiscussionsLambda);
    this.patchesTable.grantReadWriteData(this.fetchDiscussionsLambda);
    
    // Add CloudWatch permissions for metrics
    this.fetchDiscussionsLambda.addToRolePolicy(new iam.PolicyStatement({
      actions: ['cloudwatch:PutMetricData'],
      resources: ['*'],
      conditions: {
        'StringEquals': {
          'cloudwatch:namespace': 'LkmlAssistant'
        }
      }
    }));
    
    // Set up EventBridge scheduling and error handling

    // Create a Dead Letter Queue for failed Lambda executions
    const dlq = new sqs.Queue(this, 'LambdaDeadLetterQueue', {
      queueName: 'LkmlAssistant-DLQ',
      retentionPeriod: cdk.Duration.days(14),
      visibilityTimeout: cdk.Duration.minutes(5),
    });

    // 1. Schedule FetchPatches Lambda to run hourly
    const fetchPatchesHourlyRule = new events.Rule(this, 'FetchPatchesHourlyRule', {
      ruleName: 'LkmlAssistant-FetchPatchesHourly',
      schedule: events.Schedule.rate(cdk.Duration.hours(1)),
      description: 'Fetch recent patches from Patchwork API hourly',
      enabled: true,
    });
    
    fetchPatchesHourlyRule.addTarget(new targets.LambdaFunction(this.fetchPatchesLambda, {
      event: events.RuleTargetInput.fromObject({
        source: 'scheduled.hourly',
        time: new Date().toISOString(),
        page: 1,
        per_page: 10,  // Reduced from 20 to 10 for development
        process_all_pages: false,
        fetch_discussions: true
      }),
      deadLetterQueue: dlq,
      maxEventAge: cdk.Duration.hours(2),
      retryAttempts: 2,
    }));

    // 2. Schedule daily full refresh at a low-traffic time (3 AM UTC)
    const fetchPatchesDailyRule = new events.Rule(this, 'FetchPatchesDailyRule', {
      ruleName: 'LkmlAssistant-FetchPatchesDaily',
      schedule: events.Schedule.cron({ hour: '3', minute: '0' }),
      description: 'Full refresh of patches from Patchwork API daily',
      enabled: true,
    });
    
    fetchPatchesDailyRule.addTarget(new targets.LambdaFunction(this.fetchPatchesLambda, {
      event: events.RuleTargetInput.fromObject({
        source: 'scheduled.daily',
        time: new Date().toISOString(),
        page: 1,
        per_page: 20,  // Reduced from 100 to 20 for development
        process_all_pages: false,  // Changed from true to false for development
        fetch_discussions: true
      }),
      deadLetterQueue: dlq,
      maxEventAge: cdk.Duration.hours(6),
      retryAttempts: 3,
    }));

    // 3. Schedule weekly discussion refresh to update any missing discussions
    const refreshDiscussionsWeeklyRule = new events.Rule(this, 'RefreshDiscussionsWeeklyRule', {
      ruleName: 'LkmlAssistant-RefreshDiscussionsWeekly',
      schedule: events.Schedule.cron({ weekDay: 'SUN', hour: '4', minute: '30' }),
      description: 'Refresh all discussions weekly to catch any missed updates',
      enabled: true,
    });
    
    // Create a Lambda function to refresh discussions for recent patches
    const refreshDiscussionsLambda = new lambda.Function(this, 'RefreshDiscussionsFunction', {
      functionName: 'LkmlAssistant-RefreshDiscussions',
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'src/functions/refresh-discussions/index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../'), {
        exclude: [
          'infra/**', 
          'node_modules/**', 
          '.git/**',
          'docs/**',
          '.pytest_cache/**',
          'htmlcov/**',
          '**/__pycache__/**',
          '**/*.pyc'
        ]
      }),
      timeout: cdk.Duration.minutes(10),
      memorySize: 512,
      environment: {
        PATCHES_TABLE_NAME: this.patchesTable.tableName,
        DISCUSSIONS_TABLE_NAME: this.discussionsTable.tableName,
        FETCH_DISCUSSIONS_LAMBDA: this.fetchDiscussionsLambda.functionName,
      },
    });
    
    // Grant permissions
    this.patchesTable.grantReadData(refreshDiscussionsLambda);
    refreshDiscussionsLambda.addToRolePolicy(new iam.PolicyStatement({
      actions: ['lambda:InvokeFunction'],
      resources: [this.fetchDiscussionsLambda.functionArn],
    }));
    
    refreshDiscussionsWeeklyRule.addTarget(new targets.LambdaFunction(refreshDiscussionsLambda, {
      event: events.RuleTargetInput.fromObject({
        source: 'scheduled.weekly',
        time: new Date().toISOString(),
        days_to_look_back: 7,  // Reduced from 30 to 7 for development
        limit: 20  // Reduced from 200 to 20 for development
      }),
      deadLetterQueue: dlq,
      maxEventAge: cdk.Duration.hours(12),
      retryAttempts: 2,
    }));
    
    // Create CloudWatch alarms for the DLQ to monitor failures
    new cloudwatch.Alarm(this, 'DLQAlarm', {
      alarmName: 'LkmlAssistant-DLQ-NotEmpty',
      metric: dlq.metricApproximateNumberOfMessagesVisible(),
      threshold: 1,
      evaluationPeriods: 1,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
      alarmDescription: 'Alarm if the Dead Letter Queue has any messages',
    });
    
    // Create CloudWatch Dashboard
    const dashboard = createDashboard(this, {
      environment: this.environmentName,
      lambdaFunctions: [
        this.fetchPatchesLambda, 
        this.fetchDiscussionsLambda,
        refreshDiscussionsLambda
      ],
      dynamoTables: [
        this.patchesTable,
        this.discussionsTable
      ],
      deadLetterQueue: dlq
    });
    
    // Export dashboard URL for easier access
    new cdk.CfnOutput(this, 'DashboardUrl', {
      value: `https://${this.region}.console.aws.amazon.com/cloudwatch/home?region=${this.region}#dashboards:name=${dashboard.dashboardName}`,
      description: 'URL for CloudWatch Dashboard',
      exportName: `LkmlAssistant-Dashboard-${this.environmentName}`,
    });
    
    // Export table names
    new cdk.CfnOutput(this, 'PatchesTableName', {
      value: this.patchesTable.tableName,
      description: 'Name of the patches DynamoDB table',
      exportName: `LkmlAssistant-PatchesTable-${this.environmentName}`,
    });
    
    new cdk.CfnOutput(this, 'DiscussionsTableName', {
      value: this.discussionsTable.tableName,
      description: 'Name of the discussions DynamoDB table',
      exportName: `LkmlAssistant-DiscussionsTable-${this.environmentName}`,
    });
    
    // We'll add more advanced workflows in Phase 2 with Step Functions
  }
}