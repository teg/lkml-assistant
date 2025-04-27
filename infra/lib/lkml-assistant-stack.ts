import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import * as iam from 'aws-cdk-lib/aws-iam';
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
    
    // Set up EventBridge rules for scheduling
    
    // Schedule FetchPatches Lambda to run hourly
    const fetchPatchesRule = new events.Rule(this, 'FetchPatchesRule', {
      ruleName: 'LkmlAssistant-FetchPatchesHourly',
      schedule: events.Schedule.rate(cdk.Duration.hours(1)),
      description: 'Fetch patches from Patchwork API hourly',
    });
    
    fetchPatchesRule.addTarget(new targets.LambdaFunction(this.fetchPatchesLambda, {
      event: events.RuleTargetInput.fromObject({
        page: 1,
        per_page: 50,
        process_all_pages: true
      })
    }));
    
    // Note: FetchDiscussions Lambda will be triggered by the FetchPatches Lambda
    // for each patch, so we don't need to schedule it directly.
    
    // We'll add step functions or direct invocation in Phase 2
  }
}