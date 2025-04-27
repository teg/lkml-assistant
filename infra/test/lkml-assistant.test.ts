import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { LkmlAssistantStack } from '../lib/lkml-assistant-stack';

describe('LkmlAssistantStack', () => {
  let template: Template;

  // Create the stack for a development environment
  beforeAll(() => {
    const app = new cdk.App();
    const stack = new LkmlAssistantStack(app, 'TestStack', {
      environment: 'dev',
      env: { account: '123456789012', region: 'us-east-1' }
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
          KeyType: 'HASH'
        }
      ],
      BillingMode: 'PAY_PER_REQUEST',
      PointInTimeRecoverySpecification: {
        PointInTimeRecoveryEnabled: true
      },
      TimeToLiveSpecification: {
        AttributeName: 'ttl',
        Enabled: true
      }
    });

    // Verify Discussions table
    template.hasResourceProperties('AWS::DynamoDB::Table', {
      TableName: 'LkmlAssistant-Discussions-dev',
      KeySchema: [
        {
          AttributeName: 'id',
          KeyType: 'HASH'
        },
        {
          AttributeName: 'timestamp',
          KeyType: 'RANGE'
        }
      ],
      BillingMode: 'PAY_PER_REQUEST',
      PointInTimeRecoverySpecification: {
        PointInTimeRecoveryEnabled: true
      }
    });
  });

  // Test that Global Secondary Indexes are created
  test('Global Secondary Indexes Created', () => {
    // Test Patches table GSIs
    template.hasResourceProperties('AWS::DynamoDB::Table', {
      TableName: 'LkmlAssistant-Patches-dev',
      GlobalSecondaryIndexes: [
        {
          IndexName: 'SubmitterIndex',
          KeySchema: [
            {
              AttributeName: 'gsi1pk',
              KeyType: 'HASH'
            },
            {
              AttributeName: 'gsi1sk',
              KeyType: 'RANGE'
            }
          ]
        }
      ]
    });

    // Test Discussions table GSIs
    template.hasResourceProperties('AWS::DynamoDB::Table', {
      TableName: 'LkmlAssistant-Discussions-dev',
      GlobalSecondaryIndexes: [
        {
          IndexName: 'PatchIndex',
          KeySchema: [
            {
              AttributeName: 'gsi1pk',
              KeyType: 'HASH'
            },
            {
              AttributeName: 'gsi1sk',
              KeyType: 'RANGE'
            }
          ]
        }
      ]
    });
  });

  // Test that Lambda functions are created correctly
  test('Lambda Functions Created', () => {
    // Verify FetchPatches Lambda
    template.hasResourceProperties('AWS::Lambda::Function', {
      FunctionName: 'LkmlAssistant-FetchPatches-dev',
      Runtime: 'python3.9',
      Handler: 'index.handler',
      Timeout: 300,
      MemorySize: 512,
      Environment: {
        Variables: {
          PATCHES_TABLE_NAME: {
            Ref: expect.stringMatching(/^PatchesTable/)
          },
          FETCH_DISCUSSIONS_LAMBDA: 'LkmlAssistant-FetchDiscussions-dev',
          ENVIRONMENT: 'dev',
          METRIC_SOURCE: 'lambda',
          LOG_LEVEL: 'DEBUG'
        }
      }
    });

    // Verify FetchDiscussions Lambda
    template.hasResourceProperties('AWS::Lambda::Function', {
      FunctionName: 'LkmlAssistant-FetchDiscussions-dev',
      Runtime: 'python3.9',
      Handler: 'index.handler',
      Timeout: 300,
      MemorySize: 512,
      Environment: {
        Variables: {
          DISCUSSIONS_TABLE_NAME: {
            Ref: expect.stringMatching(/^DiscussionsTable/)
          },
          PATCHES_TABLE_NAME: {
            Ref: expect.stringMatching(/^PatchesTable/)
          }
        }
      }
    });
  });

  // Test that EventBridge rules are created
  test('EventBridge Rules Created', () => {
    // Verify hourly rule
    template.hasResourceProperties('AWS::Events::Rule', {
      Name: 'LkmlAssistant-FetchPatchesHourly',
      ScheduleExpression: 'rate(1 hour)',
      State: 'ENABLED',
      Targets: [
        {
          Arn: {
            'Fn::GetAtt': [expect.stringMatching(/^FetchPatchesFunction/), 'Arn']
          },
          Id: expect.any(String),
          DeadLetterConfig: {
            Arn: {
              'Fn::GetAtt': [expect.stringMatching(/^LambdaDeadLetterQueue/), 'Arn']
            }
          }
        }
      ]
    });

    // Verify daily rule
    template.hasResourceProperties('AWS::Events::Rule', {
      Name: 'LkmlAssistant-FetchPatchesDaily',
      ScheduleExpression: 'cron(0 3 * * ? *)',
      State: 'ENABLED'
    });
  });

  // Test that SQS queue is created
  test('SQS Queue Created', () => {
    template.hasResourceProperties('AWS::SQS::Queue', {
      QueueName: 'LkmlAssistant-DLQ',
      MessageRetentionPeriod: 1209600 // 14 days
    });
  });

  // Test that CloudWatch dashboard is created
  test('CloudWatch Dashboard Created', () => {
    template.hasResourceProperties('AWS::CloudWatch::Dashboard', {
      DashboardName: 'LkmlAssistant-dev'
    });
  });

  // Test that CloudWatch alarm is created
  test('CloudWatch Alarm Created', () => {
    template.hasResourceProperties('AWS::CloudWatch::Alarm', {
      AlarmName: 'LkmlAssistant-DLQ-NotEmpty',
      ComparisonOperator: 'GreaterThanThreshold',
      EvaluationPeriods: 1,
      Threshold: 1,
      MetricName: 'ApproximateNumberOfMessagesVisible'
    });
  });

  // Test resource counts to ensure we're not creating unexpected resources
  test('Resource Count Check', () => {
    // Verify number of tables created
    template.resourceCountIs('AWS::DynamoDB::Table', 2);
    
    // Verify number of Lambda functions
    template.resourceCountIs('AWS::Lambda::Function', 3); // 3 functions
    
    // Verify number of EventBridge rules
    template.resourceCountIs('AWS::Events::Rule', 3); // 3 rules
    
    // Verify number of SQS queues
    template.resourceCountIs('AWS::SQS::Queue', 1);
    
    // Verify number of dashboards
    template.resourceCountIs('AWS::CloudWatch::Dashboard', 1);
  });
});

// Test for production environment to ensure proper settings
describe('LkmlAssistantStack Production', () => {
  let template: Template;

  // Create the stack for a production environment
  beforeAll(() => {
    const app = new cdk.App();
    const stack = new LkmlAssistantStack(app, 'TestProdStack', {
      environment: 'prod',
      env: { account: '123456789012', region: 'us-east-1' }
    });
    template = Template.fromStack(stack);
  });

  // Test that production DynamoDB tables use provisioned capacity
  test('Production DynamoDB Tables Use Provisioned Capacity', () => {
    template.hasResourceProperties('AWS::DynamoDB::Table', {
      TableName: 'LkmlAssistant-Patches-prod',
      BillingMode: 'PROVISIONED',
      ProvisionedThroughput: {
        ReadCapacityUnits: 5,
        WriteCapacityUnits: 5
      }
    });
  });

  // Test that production Lambda functions have higher memory
  test('Production Lambda Functions Have Higher Memory', () => {
    template.hasResourceProperties('AWS::Lambda::Function', {
      FunctionName: 'LkmlAssistant-FetchPatches-prod',
      MemorySize: 1024
    });
  });

  // Test that production resources have deletion protection
  test('Production Tables Have Deletion Protection', () => {
    template.hasResource('AWS::DynamoDB::Table', {
      DeletionPolicy: 'Retain',
      UpdateReplacePolicy: 'Retain'
    });
  });
});