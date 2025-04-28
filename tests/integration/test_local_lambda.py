import pytest
import json
import boto3
import time
import os
from datetime import datetime
from decimal import Decimal

# Import the helper functions from test_local_dynamodb
from tests.integration.test_local_dynamodb import to_dynamodb_item, from_dynamodb_item

# Import our new direct Lambda invocation helper
from tests.integration.direct_lambda_invoker import (
    invoke_fetch_patches_lambda,
    create_test_event,
    MockLambdaContext,
)


def test_fetch_patches_lambda_direct(dynamodb_client, patches_table, setup_local_env):
    """
    Test executing the fetch-patches Lambda function code directly,
    without using LocalStack for Lambda execution.
    """
    # Configure environment for the test
    os.environ["DYNAMODB_ENDPOINT"] = "http://localhost:8000"
    os.environ["AWS_ENDPOINT_URL"] = "http://localhost:4566"

    # Create test data
    test_data = [
        {
            "id": 98765,
            "name": "Test patch from Direct Lambda",
            "submitter": {
                "id": 12345,
                "name": "Test User",
                "email": "test@example.com",
            },
            "date": datetime.utcnow().isoformat(),
            "web_url": "https://example.com/test",
            "mbox": "https://example.com/test.mbox",
            "msgid": "test-msgid@example.com",
            "content": "Test content from Direct Lambda",
        }
    ]

    # Create test event
    event = create_test_event(test_data)

    # Create context
    context = MockLambdaContext(function_name="LkmlAssistant-FetchPatches-test")

    # Call the handler using our helper
    result = invoke_fetch_patches_lambda(event, context)

    # Check the response
    assert result is not None
    assert "statusCode" in result
    assert result["statusCode"] == 200

    # Allow some time for DynamoDB operations to complete
    time.sleep(1)

    # Verify the patch was saved to DynamoDB using the client directly
    response = dynamodb_client.scan(TableName=patches_table, Limit=10)

    # Check if our test patch was saved
    found = False
    for item in response.get("Items", []):
        patch = from_dynamodb_item(item)
        if patch.get("name") == "Test patch from Direct Lambda":
            found = True
            break

    assert found, "Test patch not found in DynamoDB after Lambda execution"


def test_fetch_patches_lambda_localstack(
    lambda_client, dynamodb_client, patches_table, setup_local_env
):
    """
    Test invoking the fetch-patches Lambda function using LocalStack.
    This test will be skipped if the Lambda function is not deployed to LocalStack.
    """
    # Skip test if function doesn't exist (helpful during development)
    try:
        lambda_client.get_function(FunctionName="LkmlAssistant-FetchPatches-test")
    except Exception:
        pytest.skip("LkmlAssistant-FetchPatches-test function not deployed to LocalStack")

    # Create test payload
    payload = {
        "page": 1,
        "per_page": 2,
        "process_all_pages": False,
        "fetch_discussions": False,
        "test_mode": True,  # Add a flag to indicate we're in test mode
        "test_data": [
            {
                "id": 87654,
                "name": "Test patch from LocalStack Lambda",
                "submitter": {
                    "id": 12345,
                    "name": "Test User",
                    "email": "test@example.com",
                },
                "date": datetime.utcnow().isoformat(),
                "web_url": "https://example.com/test",
                "mbox": "https://example.com/test.mbox",
                "msgid": "test-localstack-msgid@example.com",
                "content": "Test content from LocalStack Lambda",
            }
        ],
    }

    # Invoke the Lambda function
    response = lambda_client.invoke(
        FunctionName="LkmlAssistant-FetchPatches-test", Payload=json.dumps(payload)
    )

    # Check the response
    assert response["StatusCode"] == 200

    # Parse the payload
    result = json.loads(response["Payload"].read().decode())
    assert "statusCode" in result
    assert result["statusCode"] == 200

    # Allow some time for DynamoDB operations to complete
    time.sleep(2)

    # Verify the patch was saved to DynamoDB using the client directly
    response = dynamodb_client.scan(TableName=patches_table, Limit=10)

    # Check if our test patch was saved
    found = False
    for item in response.get("Items", []):
        patch = from_dynamodb_item(item)
        if patch.get("name") == "Test patch from LocalStack Lambda":
            found = True
            break

    assert found, "Test patch not found in DynamoDB after LocalStack Lambda execution"
