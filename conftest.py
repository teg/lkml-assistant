"""
Configure pytest fixtures and environment for all tests.
"""

import os
import pytest
import boto3
from moto import mock_dynamodb, mock_cloudwatch

# Configure AWS credentials for local testing
os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
os.environ['AWS_SECURITY_TOKEN'] = 'testing'
os.environ['AWS_SESSION_TOKEN'] = 'testing'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'  # Set a default region

@pytest.fixture(scope='function')
def aws_credentials():
    """Mocked AWS Credentials for boto3."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

@pytest.fixture(scope='function')
def dynamodb(aws_credentials):
    """DynamoDB mock."""
    with mock_dynamodb():
        yield boto3.resource('dynamodb', region_name='us-east-1')

@pytest.fixture(scope='function')
def cloudwatch(aws_credentials):
    """CloudWatch mock."""
    with mock_cloudwatch():
        yield boto3.client('cloudwatch', region_name='us-east-1')