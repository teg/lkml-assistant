import os
import pytest
import boto3
import subprocess
import time
import json
from datetime import datetime

# Set environment variables for tests
os.environ["AWS_ACCESS_KEY_ID"] = "test"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["PATCHES_TABLE_NAME"] = "LkmlAssistant-Patches-test"
os.environ["DISCUSSIONS_TABLE_NAME"] = "LkmlAssistant-Discussions-test"
os.environ["ENVIRONMENT"] = "test"
os.environ["LOG_LEVEL"] = "DEBUG"


@pytest.fixture(scope="session")
def setup_local_env():
    """
    Set up the local test environment before tests and clean up afterwards.
    """
    # Run the setup script
    print("Setting up local test environment...")
    subprocess.run(["bash", "./scripts/setup_local_test_env.sh"], check=True)
    
    # Wait a bit to ensure everything is ready
    time.sleep(5)
    
    yield
    
    # Clean up after tests
    print("Cleaning up local test environment...")
    subprocess.run(["bash", "./scripts/clean_local_test_env.sh"], check=True)


@pytest.fixture(scope="function")
def dynamodb_client(setup_local_env):
    """
    Create a DynamoDB client configured to use the local DynamoDB instance.
    """
    return boto3.client(
        'dynamodb',
        endpoint_url='http://localhost:8000',
        region_name='us-east-1',
        aws_access_key_id='test',
        aws_secret_access_key='test'
    )


@pytest.fixture(scope="function")
def lambda_client(setup_local_env):
    """
    Create a Lambda client configured to use the local LocalStack instance.
    """
    return boto3.client(
        'lambda',
        endpoint_url='http://localhost:4566',
        region_name='us-east-1',
        aws_access_key_id='test',
        aws_secret_access_key='test'
    )


@pytest.fixture(scope="function")
def patches_table(dynamodb_client):
    """
    Get the DynamoDB patches table and ensure it's empty for each test.
    """
    # Clear the table
    table_name = os.environ["PATCHES_TABLE_NAME"]
    try:
        response = dynamodb_client.scan(TableName=table_name, ProjectionExpression="id")
        items = response.get('Items', [])
        for item in items:
            patch_id = item['id']['S']
            dynamodb_client.delete_item(
                TableName=table_name,
                Key={'id': {'S': patch_id}}
            )
    except Exception as e:
        print(f"Error clearing patches table: {str(e)}")
    
    return table_name


@pytest.fixture(scope="function")
def discussions_table(dynamodb_client):
    """
    Get the DynamoDB discussions table and ensure it's empty for each test.
    """
    # Clear the table
    table_name = os.environ["DISCUSSIONS_TABLE_NAME"]
    try:
        response = dynamodb_client.scan(
            TableName=table_name, 
            ProjectionExpression="id, #ts",
            ExpressionAttributeNames={"#ts": "timestamp"}
        )
        items = response.get('Items', [])
        for item in items:
            discussion_id = item['id']['S']
            timestamp = item['timestamp']['S']
            dynamodb_client.delete_item(
                TableName=table_name,
                Key={
                    'id': {'S': discussion_id},
                    'timestamp': {'S': timestamp}
                }
            )
    except Exception as e:
        print(f"Error clearing discussions table: {str(e)}")
    
    return table_name


@pytest.fixture(scope="function")
def sample_patch_data():
    """
    Create sample patch data for testing.
    """
    now = datetime.utcnow().isoformat()
    return {
        "id": "12345",
        "name": "Test Patch",
        "submitterId": "67890",
        "submitterName": "Test Submitter",
        "submitterEmail": "test@example.com",
        "submittedAt": now,
        "lastUpdatedAt": now,
        "status": "NEW",
        "url": "https://example.com/patch/12345",
        "webUrl": "https://example.com/patch/12345/web",
        "mboxUrl": "https://example.com/patch/12345/mbox",
        "messageId": "test-message-id@example.com",
        "content": "This is a test patch content",
        "discussionCount": 0,
        "gsi1pk": "SUBMITTER#67890",
        "gsi1sk": f"DATE#{now}",
        "gsi3pk": "STATUS#NEW",
        "gsi3sk": f"DATE#{now}"
    }


@pytest.fixture(scope="function")
def sample_discussion_data():
    """
    Create sample discussion data for testing.
    """
    now = datetime.utcnow().isoformat()
    return {
        "id": "disc-12345",
        "timestamp": now,
        "patchId": "12345",
        "subject": "Re: Test Patch",
        "author": "Test Author",
        "authorEmail": "author@example.com",
        "date": now,
        "content": "This is a test discussion content",
        "messageId": "test-discussion-id@example.com",
        "threadId": "thread-12345",
        "parentId": None,
        "gsi1pk": "PATCH#12345",
        "gsi1sk": f"DATE#{now}",
        "gsi2pk": "THREAD#thread-12345",
        "gsi2sk": f"DATE#{now}",
        "gsi3pk": "AUTHOR#author@example.com",
        "gsi3sk": f"DATE#{now}"
    }