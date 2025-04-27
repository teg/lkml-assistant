import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as sqs from 'aws-cdk-lib/aws-sqs';

/**
 * Props for creating a CloudWatch dashboard
 */
export interface DashboardProps {
  environment: string;
  lambdaFunctions: lambda.Function[];
  dynamoTables: dynamodb.Table[];
  deadLetterQueue?: sqs.Queue;
}

/**
 * Creates a CloudWatch dashboard for monitoring the application
 */
export function createDashboard(scope: Construct, props: DashboardProps): cloudwatch.Dashboard {
  const { environment, lambdaFunctions, dynamoTables, deadLetterQueue } = props;
  
  // Create dashboard
  const dashboard = new cloudwatch.Dashboard(scope, `LkmlAssistantDashboard-${environment}`, {
    dashboardName: `LkmlAssistant-${environment}`,
  });

  // Add Lambda metrics
  const lambdaWidgets: cloudwatch.IWidget[] = lambdaFunctions.map(fn => {
    return new cloudwatch.GraphWidget({
      title: `Lambda: ${fn.functionName}`,
      left: [
        fn.metricInvocations({
          statistic: 'Sum',
          period: cdk.Duration.minutes(1),
          label: 'Invocations',
          color: '#2ca02c'
        }),
        fn.metricErrors({
          statistic: 'Sum',
          period: cdk.Duration.minutes(1),
          label: 'Errors',
          color: '#d62728'
        }),
      ],
      right: [
        fn.metricDuration({
          statistic: 'Average',
          period: cdk.Duration.minutes(1),
          label: 'Duration (avg)',
          color: '#1f77b4'
        }),
        fn.metricDuration({
          statistic: 'Maximum',
          period: cdk.Duration.minutes(1),
          label: 'Duration (max)',
          color: '#ff7f0e'
        }),
      ],
      width: 12,
    });
  });
  
  // Add DynamoDB metrics
  const dynamoWidgets: cloudwatch.IWidget[] = dynamoTables.map(table => {
    return new cloudwatch.GraphWidget({
      title: `DynamoDB: ${table.tableName}`,
      left: [
        table.metricConsumedReadCapacityUnits({
          statistic: 'Sum',
          period: cdk.Duration.minutes(5),
          label: 'Read Capacity',
          color: '#1f77b4'
        }),
        table.metricConsumedWriteCapacityUnits({
          statistic: 'Sum',
          period: cdk.Duration.minutes(5),
          label: 'Write Capacity',
          color: '#ff7f0e'
        }),
      ],
      right: [
        table.metricThrottledRequests({
          statistic: 'Sum',
          period: cdk.Duration.minutes(5),
          label: 'Throttled Requests',
          color: '#d62728'
        }),
      ],
      width: 12,
    });
  });
  
  // Add DLQ metrics if provided
  const dlqWidgets: cloudwatch.IWidget[] = [];
  if (deadLetterQueue) {
    dlqWidgets.push(
      new cloudwatch.GraphWidget({
        title: 'Dead Letter Queue',
        left: [
          deadLetterQueue.metricNumberOfMessagesReceived({
            statistic: 'Sum',
            period: cdk.Duration.minutes(5),
            label: 'Messages Received',
            color: '#d62728'
          }),
          deadLetterQueue.metricApproximateNumberOfMessagesVisible({
            statistic: 'Maximum',
            period: cdk.Duration.minutes(5),
            label: 'Messages Visible',
            color: '#ff7f0e'
          }),
        ],
        width: 24,
      })
    );
  }
  
  // Add application-specific metrics
  const appWidgets: cloudwatch.IWidget[] = [
    new cloudwatch.GraphWidget({
      title: 'API Metrics',
      left: [
        new cloudwatch.Metric({
          namespace: 'LkmlAssistant',
          metricName: 'ApiCalls',
          dimensionsMap: {
            'Environment': environment,
          },
          statistic: 'Sum',
          period: cdk.Duration.minutes(5),
          label: 'API Calls',
          color: '#2ca02c'
        }),
        new cloudwatch.Metric({
          namespace: 'LkmlAssistant',
          metricName: 'ApiLatency',
          dimensionsMap: {
            'Environment': environment,
          },
          statistic: 'Average',
          period: cdk.Duration.minutes(5),
          label: 'API Latency (avg)',
          color: '#1f77b4'
        }),
      ],
      width: 12,
    }),
    new cloudwatch.GraphWidget({
      title: 'Application Metrics',
      left: [
        new cloudwatch.Metric({
          namespace: 'LkmlAssistant',
          metricName: 'RecordCount',
          dimensionsMap: {
            'Environment': environment,
          },
          statistic: 'Sum',
          period: cdk.Duration.minutes(5),
          label: 'Records Processed',
          color: '#2ca02c'
        }),
      ],
      width: 12,
    }),
  ];
  
  // Combine all widgets
  dashboard.addWidgets(
    new cloudwatch.TextWidget({
      markdown: `# LKML Assistant Dashboard - ${environment.toUpperCase()}`,
      width: 24,
      height: 1,
    }),
    ...lambdaWidgets,
    ...dynamoWidgets,
    ...dlqWidgets,
    ...appWidgets
  );
  
  return dashboard;
}