import pytest
import json
import boto3
import time
from datetime import datetime
from src.repositories import patch_repository, discussion_repository


def test_fetch_patches_lambda(lambda_client, patches_table, setup_local_env):
    """
    Test invoking the fetch-patches Lambda function locally.
    This test requires that the fetch-patches function be deployed to LocalStack.
    """
    # Skip test if function doesn't exist (helpful during development)
    try:
        lambda_client.get_function(FunctionName='LkmlAssistant-FetchPatches-test')
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
            }
        ]
    }

    # Invoke the Lambda function
    response = lambda_client.invoke(
        FunctionName='LkmlAssistant-FetchPatches-test',
        Payload=json.dumps(payload)
    )

    # Check the response
    assert response['StatusCode'] == 200
    
    # Parse the payload
    result = json.loads(response['Payload'].read().decode())
    assert 'statusCode' in result
    assert result['statusCode'] == 200
    
    # Allow some time for DynamoDB operations to complete
    time.sleep(2)
    
    # Verify the patch was saved to DynamoDB
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url='http://localhost:8000',
        region_name='us-east-1',
        aws_access_key_id='test',
        aws_secret_access_key='test'
    )
    
    table = dynamodb.Table('LkmlAssistant-Patches-test')
    response = table.scan(Limit=10)
    
    # Check if our test patch was saved
    found = False
    for item in response.get('Items', []):
        if item.get('name') == "Test patch from Lambda":
            found = True
            break
    
    assert found, "Test patch not found in DynamoDB after Lambda execution"