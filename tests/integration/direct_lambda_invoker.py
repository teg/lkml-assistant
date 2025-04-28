"""
Test helper to invoke Lambda functions directly without using AWS Lambda.
This bypasses the need for LocalStack by directly calling the handler functions.
"""
import os
import sys
import json
import boto3
import importlib.util
from datetime import datetime
from typing import Dict, Any

# Add project root to Python path so we can import modules correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class MockLambdaContext:
    """Mock Lambda context for testing"""
    def __init__(self, function_name="test-function"):
        self.function_name = function_name
        self.function_version = "$LATEST"
        self.memory_limit_in_mb = 128
        self.invoked_function_arn = f"arn:aws:lambda:us-east-1:123456789012:function:{function_name}"
        self.aws_request_id = "00000000-0000-0000-0000-000000000000"


def load_lambda_module(function_path):
    """
    Load a Lambda function module directly for testing.
    """
    # Get the absolute path to the Lambda function file
    file_path = os.path.join(os.getcwd(), function_path)

    # Extract the module name from the file path
    module_name = os.path.splitext(os.path.basename(file_path))[0]

    # Load the module dynamically
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        raise ImportError(f"Could not find Lambda module at: {file_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def invoke_fetch_patches_lambda(event, context=None):
    """
    Directly invoke the fetch-patches Lambda function code.
    """
    # Set environment variables for testing
    os.environ["PATCHES_TABLE_NAME"] = "LkmlAssistant-Patches-test"
    os.environ["FETCH_DISCUSSIONS_LAMBDA"] = "LkmlAssistant-FetchDiscussions-test"
    os.environ["ENVIRONMENT"] = "test"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["DYNAMODB_ENDPOINT"] = "http://localhost:8000"
    os.environ["AWS_ENDPOINT_URL"] = "http://localhost:4566"

    # Create context if not provided
    if context is None:
        context = MockLambdaContext(function_name="LkmlAssistant-FetchPatches-test")

    # Save original boto3 client
    original_client = boto3.client

    # Define mock client for Lambda
    class MockLambdaClient:
        def invoke(self, **kwargs):
            return {"StatusCode": 202}

    # Patch boto3 resource
    original_resource = boto3.resource

    # Patch boto3.client to return our mock for Lambda and configure DynamoDB
    def mock_client(service_name, *args, **kwargs):
        if service_name == "lambda":
            return MockLambdaClient()
        elif service_name == "dynamodb":
            # Make sure we use the local DynamoDB endpoint
            # Create a new kwargs dict to avoid parameter conflicts
            new_kwargs = {
                "endpoint_url": "http://localhost:8000",
                "region_name": "us-east-1",
                "aws_access_key_id": "test",
                "aws_secret_access_key": "test"
            }
            # Only add other kwargs that don't conflict
            for k, v in kwargs.items():
                if k not in new_kwargs:
                    new_kwargs[k] = v

            return original_client(service_name, *args, **new_kwargs)
        return original_client(service_name, *args, **kwargs)

    # Patch boto3.resource
    def mock_resource(service_name, *args, **kwargs):
        if service_name == "dynamodb":
            # Make sure we use the local DynamoDB endpoint
            # Create a new kwargs dict to avoid parameter conflicts
            new_kwargs = {
                "endpoint_url": "http://localhost:8000",
                "region_name": "us-east-1",
                "aws_access_key_id": "test",
                "aws_secret_access_key": "test"
            }
            # Only add other kwargs that don't conflict
            for k, v in kwargs.items():
                if k not in new_kwargs:
                    new_kwargs[k] = v

            return original_resource(service_name, *args, **new_kwargs)
        return original_resource(service_name, *args, **kwargs)

    # Apply the patches
    boto3.client = mock_client
    boto3.resource = mock_resource

    try:
        # Load and execute the Lambda function
        from src.functions.fetch_patches import index
        result = index.handler(event, context)
        return result
    finally:
        # Restore the original boto3 functions
        boto3.client = original_client
        boto3.resource = original_resource


def create_test_event(test_data=None):
    """
    Create a test event for the fetch-patches Lambda function.
    """
    if test_data is None:
        # Default test data
        test_data = [{
            "id": 98765,
            "name": "Test patch from Lambda",
            "submitter": {
                "id": 12345,
                "name": "Test User",
                "email": "test@example.com"
            },
            "date": datetime.utcnow().isoformat(),
            "web_url": "https://example.com/test",
            "mbox": "https://example.com/test.mbox",
            "msgid": "test-msgid@example.com",
            "content": "Test content from Lambda"
        }]

    return {
        "page": 1,
        "per_page": 2,
        "process_all_pages": False,
        "fetch_discussions": False,
        "test_mode": True,
        "test_data": test_data
    }
