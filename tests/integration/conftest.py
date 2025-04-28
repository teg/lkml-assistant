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
    This assumes DynamoDB is already running locally in a Podman container.
    """
    print("Setting up local test environment...")
    # We're not going to run the scripts since they're failing
    # Instead assume DynamoDB is already running via podman

    # Create Patches table
    dynamodb = boto3.client(
        'dynamodb',
        endpoint_url='http://localhost:8000',
        region_name='us-east-1',
        aws_access_key_id='test',
        aws_secret_access_key='test'
    )

    # Delete tables if they exist
    for table_name in ['LkmlAssistant-Patches-test', 'LkmlAssistant-Discussions-test']:
        try:
            dynamodb.delete_table(TableName=table_name)
            print(f"Deleted existing table: {table_name}")
            time.sleep(1)
        except Exception:
            pass

    # Create Patches table
    try:
        dynamodb.create_table(
            TableName='LkmlAssistant-Patches-test',
            AttributeDefinitions=[
                {'AttributeName': 'id', 'AttributeType': 'S'},
                {'AttributeName': 'gsi1pk', 'AttributeType': 'S'},
                {'AttributeName': 'gsi1sk', 'AttributeType': 'S'},
                {'AttributeName': 'gsi2pk', 'AttributeType': 'S'},
                {'AttributeName': 'gsi2sk', 'AttributeType': 'S'},
                {'AttributeName': 'gsi3pk', 'AttributeType': 'S'},
                {'AttributeName': 'gsi3sk', 'AttributeType': 'S'}
            ],
            KeySchema=[
                {'AttributeName': 'id', 'KeyType': 'HASH'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'SubmitterIndex',
                    'KeySchema': [
                        {'AttributeName': 'gsi1pk', 'KeyType': 'HASH'},
                        {'AttributeName': 'gsi1sk', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                },
                {
                    'IndexName': 'SeriesIndex',
                    'KeySchema': [
                        {'AttributeName': 'gsi2pk', 'KeyType': 'HASH'},
                        {'AttributeName': 'gsi2sk', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                },
                {
                    'IndexName': 'StatusIndex',
                    'KeySchema': [
                        {'AttributeName': 'gsi3pk', 'KeyType': 'HASH'},
                        {'AttributeName': 'gsi3sk', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print("Created Patches table")
    except Exception as e:
        print(f"Error creating Patches table: {str(e)}")

    # Create Discussions table
    try:
        dynamodb.create_table(
            TableName='LkmlAssistant-Discussions-test',
            AttributeDefinitions=[
                {'AttributeName': 'id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'},
                {'AttributeName': 'gsi1pk', 'AttributeType': 'S'},
                {'AttributeName': 'gsi1sk', 'AttributeType': 'S'},
                {'AttributeName': 'gsi2pk', 'AttributeType': 'S'},
                {'AttributeName': 'gsi2sk', 'AttributeType': 'S'},
                {'AttributeName': 'gsi3pk', 'AttributeType': 'S'},
                {'AttributeName': 'gsi3sk', 'AttributeType': 'S'}
            ],
            KeySchema=[
                {'AttributeName': 'id', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'PatchIndex',
                    'KeySchema': [
                        {'AttributeName': 'gsi1pk', 'KeyType': 'HASH'},
                        {'AttributeName': 'gsi1sk', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                },
                {
                    'IndexName': 'ThreadIndex',
                    'KeySchema': [
                        {'AttributeName': 'gsi2pk', 'KeyType': 'HASH'},
                        {'AttributeName': 'gsi2sk', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                },
                {
                    'IndexName': 'AuthorIndex',
                    'KeySchema': [
                        {'AttributeName': 'gsi3pk', 'KeyType': 'HASH'},
                        {'AttributeName': 'gsi3sk', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print("Created Discussions table")
    except Exception as e:
        print(f"Error creating Discussions table: {str(e)}")

    # Wait for tables to be ACTIVE
    print("Waiting for tables to be ready...")
    time.sleep(2)

    yield

    # Clean up after tests
    print("Cleaning up local test environment...")
    try:
        dynamodb.delete_table(TableName='LkmlAssistant-Patches-test')
        dynamodb.delete_table(TableName='LkmlAssistant-Discussions-test')
    except Exception as e:
        print(f"Error cleaning up tables: {str(e)}")


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
    Note: We'll mock this for now since we're not using LocalStack
    """
    # Using moto to mock AWS services instead of actual LocalStack
    import boto3
    from unittest.mock import MagicMock

    mock_client = MagicMock()
    mock_client.invoke.return_value = {
        'StatusCode': 200,
        'Payload': MagicMock()
    }
    mock_client.Payload.read.return_value = json.dumps({"statusCode": 200}).encode()

    return mock_client


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
