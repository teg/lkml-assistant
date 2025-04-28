#!/bin/bash
set -euo pipefail

# Get the AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_REGION:-us-east-1}

echo "Cleaning up CDK bootstrap resources for account $ACCOUNT_ID in region $AWS_REGION"

# Step 1: Delete the CloudFormation stack if it exists in a failed state
echo "Checking for CDKToolkit stack..."
if aws cloudformation describe-stacks --stack-name CDKToolkit --region $AWS_REGION 2>/dev/null; then
  echo "Deleting CDKToolkit stack..."
  aws cloudformation delete-stack --stack-name CDKToolkit --region $AWS_REGION
  echo "Waiting for stack deletion to complete..."
  aws cloudformation wait stack-delete-complete --stack-name CDKToolkit --region $AWS_REGION
  echo "Stack deleted successfully."
else
  echo "CDKToolkit stack not found or not accessible."
fi

# Step 2: Delete the S3 bucket if it exists
BUCKET_NAME="cdk-hnb659fds-assets-${ACCOUNT_ID}-${AWS_REGION}"
echo "Checking for S3 bucket $BUCKET_NAME..."
if aws s3api head-bucket --bucket $BUCKET_NAME 2>/dev/null; then
  echo "Emptying S3 bucket $BUCKET_NAME..."
  aws s3 rm s3://$BUCKET_NAME --recursive
  
  echo "Deleting S3 bucket $BUCKET_NAME..."
  aws s3api delete-bucket --bucket $BUCKET_NAME
  echo "Bucket deleted successfully."
else
  echo "S3 bucket not found or not accessible."
fi

# Step 3: Check for ECR repositories
echo "Checking for CDK ECR repositories..."
REPOS=$(aws ecr describe-repositories --region $AWS_REGION --query "repositories[?contains(repositoryName, 'cdk-')].repositoryName" --output text)
if [ -n "$REPOS" ]; then
  echo "Found CDK ECR repositories: $REPOS"
  for REPO in $REPOS; do
    echo "Deleting repository $REPO..."
    aws ecr delete-repository --repository-name $REPO --force --region $AWS_REGION
  done
  echo "ECR repositories deleted successfully."
else
  echo "No CDK ECR repositories found."
fi

echo "Cleanup completed. You can now run 'cdk bootstrap' again."