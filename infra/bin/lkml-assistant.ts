#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { LkmlAssistantStack } from '../lib/lkml-assistant-stack';

const app = new cdk.App();

// Get environment from context or default to dev
const environment = app.node.tryGetContext('environment') || 'dev';

// Get AWS account and region
const account = process.env.CDK_DEFAULT_ACCOUNT || process.env.AWS_ACCOUNT_ID;
const region = process.env.CDK_DEFAULT_REGION || process.env.AWS_REGION || 'us-east-1';

// Define stack name based on environment
const stackName = `LkmlAssistantStack-${environment}`;

// Create the stack
new LkmlAssistantStack(app, stackName, {
  // Pass environment-specific configuration
  environment: environment,
  
  // Set AWS account and region
  env: { 
    account: account, 
    region: region 
  },
  
  // Add description
  description: `LKML Assistant infrastructure for ${environment} environment`,
  
  // Add termination protection for production
  terminationProtection: environment === 'prod',
});