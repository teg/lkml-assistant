import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as path from 'path';

export class LkmlAssistantStack extends cdk.Stack {
  // Make tables public so they can be accessed by other constructs
  public readonly patchesTable: dynamodb.Table;
  public readonly discussionsTable: dynamodb.Table;
  public readonly fetchPatchesLambda: lambda.Function;
  public readonly fetchDiscussionsLambda: lambda.Function;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Define DynamoDB tables
    this.patchesTable = new dynamodb.Table(this, 'PatchesTable', {
      tableName: 'LkmlAssistant-Patches',
      partitionKey: { name: 'id', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // NOT recommended for production
      pointInTimeRecovery: true,
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
      tableName: 'LkmlAssistant-Discussions',
      partitionKey: { name: 'id', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'timestamp', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // NOT recommended for production
      pointInTimeRecovery: true,
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
    
    // 1. Fetch Patches Lambda
    this.fetchPatchesLambda = new lambda.Function(this, 'FetchPatchesFunction', {
      functionName: 'LkmlAssistant-FetchPatches',
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../src/functions/fetch-patches')),
      timeout: cdk.Duration.seconds(300),
      memorySize: 512,
      environment: {
        PATCHES_TABLE_NAME: this.patchesTable.tableName,
        FETCH_DISCUSSIONS_LAMBDA: 'LkmlAssistant-FetchDiscussions',
      },
    });
    
    // Grant DynamoDB permissions to FetchPatches Lambda
    this.patchesTable.grantWriteData(this.fetchPatchesLambda);
    
    // Grant Lambda permissions to invoke other Lambdas
    this.fetchPatchesLambda.addToRolePolicy(new iam.PolicyStatement({
      actions: ['lambda:InvokeFunction'],
      resources: ['*'],  // In a production environment, this should be restricted to specific Lambda ARNs
    }));
    
    // 2. Fetch Discussions Lambda
    this.fetchDiscussionsLambda = new lambda.Function(this, 'FetchDiscussionsFunction', {
      functionName: 'LkmlAssistant-FetchDiscussions',
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../src/functions/fetch-discussions')),
      timeout: cdk.Duration.seconds(300),
      memorySize: 512,
      environment: {
        DISCUSSIONS_TABLE_NAME: this.discussionsTable.tableName,
        PATCHES_TABLE_NAME: this.patchesTable.tableName,
      },
    });
    
    // Grant DynamoDB permissions to FetchDiscussions Lambda
    this.discussionsTable.grantWriteData(this.fetchDiscussionsLambda);
    this.patchesTable.grantReadWriteData(this.fetchDiscussionsLambda);
    
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
        time: events.ScheduleExpression.field('time'),
        page: 1,
        per_page: 20,
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
        time: events.ScheduleExpression.field('time'),
        page: 1,
        per_page: 100,
        process_all_pages: true,
        fetch_discussions: true
      }),
      deadLetterQueue: dlq,
      maxEventAge: cdk.Duration.hours(6),
      retryAttempts: 3,
    }));

    // 3. Schedule weekly discussion refresh to update any missing discussions
    const refreshDiscussionsWeeklyRule = new events.Rule(this, 'RefreshDiscussionsWeeklyRule', {
      ruleName: 'LkmlAssistant-RefreshDiscussionsWeekly',
      schedule: events.Schedule.cron({ day: 'SUN', hour: '4', minute: '30' }),
      description: 'Refresh all discussions weekly to catch any missed updates',
      enabled: true,
    });
    
    // Create a Lambda function to refresh discussions for recent patches
    const refreshDiscussionsLambda = new lambda.Function(this, 'RefreshDiscussionsFunction', {
      functionName: 'LkmlAssistant-RefreshDiscussions',
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../src/functions/refresh-discussions')),
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
        time: events.ScheduleExpression.field('time'),
        days_to_look_back: 30,
        limit: 200
      }),
      deadLetterQueue: dlq,
      maxEventAge: cdk.Duration.hours(12),
      retryAttempts: 2,
    }));
    
    // Create CloudWatch alarms for the DLQ to monitor failures
    const dlqAlarm = new cloudwatch.Alarm(this, 'DLQAlarm', {
      alarmName: 'LkmlAssistant-DLQ-NotEmpty',
      metric: dlq.metricApproximateNumberOfMessagesVisible(),
      threshold: 1,
      evaluationPeriods: 1,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
      alarmDescription: 'Alarm if the Dead Letter Queue has any messages',
    });
    
    // We'll add more advanced workflows in Phase 2 with Step Functions
  }
}