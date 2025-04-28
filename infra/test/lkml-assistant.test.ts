import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';
import { LkmlAssistantStack } from '../lib/lkml-assistant-stack';

describe('LkmlAssistantStack', () => {
  let template: Template;

  // Create the stack for a development environment
  beforeAll(() => {
    const app = new cdk.App({
      context: {
        '@aws-cdk/core:newStyleStackSynthesis': false,
      },
    });
    const stack = new LkmlAssistantStack(app, 'TestStack', {
      environmentName: 'dev',
    });
    template = Template.fromStack(stack);
  });

  // Test that the DynamoDB tables are created correctly
  test('DynamoDB Tables Created', () => {
    // Verify Patches table
    template.hasResourceProperties('AWS::DynamoDB::Table', {
      TableName: 'LkmlAssistant-Patches-dev',
      KeySchema: [
        {
          AttributeName: 'id',
          KeyType: 'HASH',
        },
      ],
      BillingMode: 'PAY_PER_REQUEST',
      PointInTimeRecoverySpecification: {
        PointInTimeRecoveryEnabled: true,
      },
      TimeToLiveSpecification: {
        AttributeName: 'ttl',
        Enabled: true,
      },
    });

    // Verify Discussions table
    template.hasResourceProperties('AWS::DynamoDB::Table', {
      TableName: 'LkmlAssistant-Discussions-dev',
      KeySchema: [
        {
          AttributeName: 'id',
          KeyType: 'HASH',
        },
        {
          AttributeName: 'timestamp',
          KeyType: 'RANGE',
        },
      ],
      BillingMode: 'PAY_PER_REQUEST',
      PointInTimeRecoverySpecification: {
        PointInTimeRecoveryEnabled: true,
      },
    });
  });

  // Test that Global Secondary Indexes are created
  test('Global Secondary Indexes Created', () => {
    // Test that at least one table has a SubmitterIndex
    template.hasResourceProperties('AWS::DynamoDB::Table', {
      GlobalSecondaryIndexes: Match.arrayWith([
        Match.objectLike({
          IndexName: 'SubmitterIndex',
        }),
      ]),
    });

    // Test that at least one table has a PatchIndex
    template.hasResourceProperties('AWS::DynamoDB::Table', {
      GlobalSecondaryIndexes: Match.arrayWith([
        Match.objectLike({
          IndexName: 'PatchIndex',
        }),
      ]),
    });
  });

  // Test that Lambda functions are created correctly
  test('Lambda Functions Created', () => {
    // Verify FetchPatches Lambda
    template.hasResourceProperties('AWS::Lambda::Function', {
      FunctionName: 'LkmlAssistant-FetchPatches-dev',
      Runtime: 'python3.9',
      Handler: 'src/functions/fetch-patches/index.handler',
      Timeout: 300,
      MemorySize: 512,
      Environment: Match.objectLike({
        Variables: Match.objectLike({
          ENVIRONMENT: 'dev',
          FETCH_DISCUSSIONS_LAMBDA: 'LkmlAssistant-FetchDiscussions-dev',
          LOG_LEVEL: 'DEBUG',
        }),
      }),
    });

    // Verify FetchDiscussions Lambda
    template.hasResourceProperties('AWS::Lambda::Function', {
      FunctionName: 'LkmlAssistant-FetchDiscussions-dev',
      Runtime: 'python3.9',
      Handler: 'src/functions/fetch-discussions/index.handler',
      Timeout: 300,
      MemorySize: 512,
    });
  });

  // Test that EventBridge rules are created
  test('EventBridge Rules Created', () => {
    // Verify hourly rule exists
    template.hasResourceProperties('AWS::Events::Rule', {
      Name: 'LkmlAssistant-FetchPatchesHourly',
      ScheduleExpression: 'rate(1 hour)',
      State: 'ENABLED',
    });

    // Verify daily rule exists
    template.hasResourceProperties('AWS::Events::Rule', {
      Name: 'LkmlAssistant-FetchPatchesDaily',
      ScheduleExpression: 'cron(0 3 * * ? *)',
      State: 'ENABLED',
    });
  });

  // Test that SQS queue is created
  test('SQS Queue Created', () => {
    template.hasResourceProperties('AWS::SQS::Queue', {
      QueueName: 'LkmlAssistant-DLQ',
      MessageRetentionPeriod: 1209600, // 14 days
    });
  });

  // Test that CloudWatch dashboard is created
  test('CloudWatch Dashboard Created', () => {
    template.hasResourceProperties('AWS::CloudWatch::Dashboard', {
      DashboardName: 'LkmlAssistant-dev',
    });
  });

  // Test that CloudWatch alarm is created
  test('CloudWatch Alarm Created', () => {
    template.hasResourceProperties('AWS::CloudWatch::Alarm', {
      AlarmName: 'LkmlAssistant-DLQ-NotEmpty',
      EvaluationPeriods: 1,
      Threshold: 1,
    });
  });

  // Test resource counts to ensure we're not creating unexpected resources
  test('Resource Count Check', () => {
    // Verify number of tables created is at least 2
    template.resourceCountIs('AWS::DynamoDB::Table', 2);

    // Verify number of Lambda functions
    const lambdaCount = Object.entries(template.findResources('AWS::Lambda::Function')).length;
    expect(lambdaCount).toBeGreaterThanOrEqual(3);

    // Verify number of EventBridge rules is at least 3
    template.resourceCountIs('AWS::Events::Rule', 3);

    // Verify number of SQS queues is at least 1
    template.resourceCountIs('AWS::SQS::Queue', 1);

    // Verify number of dashboards is at least 1
    template.resourceCountIs('AWS::CloudWatch::Dashboard', 1);
  });
});

// Test for production environment to ensure proper settings
describe('LkmlAssistantStack Production', () => {
  let template: Template;

  // Create the stack for a production environment
  beforeAll(() => {
    const app = new cdk.App({
      context: {
        '@aws-cdk/core:newStyleStackSynthesis': false,
      },
    });
    const stack = new LkmlAssistantStack(app, 'TestProdStack', {
      environmentName: 'prod',
    });
    template = Template.fromStack(stack);
  });

  // Test that production DynamoDB tables use provisioned capacity
  test('Production DynamoDB Tables Use Provisioned Capacity', () => {
    template.hasResourceProperties('AWS::DynamoDB::Table', {
      ProvisionedThroughput: {
        ReadCapacityUnits: 5,
        WriteCapacityUnits: 5,
      },
    });
  });

  // Test that production Lambda functions have higher memory
  test('Production Lambda Functions Have Higher Memory', () => {
    template.hasResourceProperties('AWS::Lambda::Function', {
      MemorySize: 1024,
    });
  });

  // Test that production resources have deletion protection
  test('Production Tables Have Deletion Protection', () => {
    template.hasResource('AWS::DynamoDB::Table', {
      DeletionPolicy: 'Retain',
      UpdateReplacePolicy: 'Retain',
    });
  });
});
