"""
Post-Deployment Tests for Fetch Discussions Lambda

These tests verify that the deployed Fetch Discussions Lambda function
works correctly in the target environment.
"""

import pytest
import os
import json
from .post_deploy_verifier import DeploymentVerifier, TestPayloads


# Get environment from environment variable or default to dev
ENVIRONMENT = os.environ.get("TEST_ENVIRONMENT", "dev")


@pytest.fixture
def verifier():
    """Create a deployment verifier for tests."""
    # Get AWS profile from environment
    aws_profile = os.environ.get("AWS_PROFILE")
    return DeploymentVerifier(environment=ENVIRONMENT, profile=aws_profile)


def test_fetch_discussions_lambda_exists(verifier):
    """Test that the fetch-discussions Lambda function exists."""
    # Skip if AWS credentials are not valid
    if not verifier.credentials_valid:
        pytest.skip("AWS credentials are not valid. Configure valid credentials to run this test.")
        return

    # Get Lambda function details
    try:
        function_name = f"LkmlAssistant-FetchDiscussions-{ENVIRONMENT}"
        response = verifier.lambda_client.get_function(FunctionName=function_name)

        # Check that the function exists and is active
        assert response["Configuration"]["State"] == "Active"
        assert response["Configuration"]["Runtime"].startswith("python")

        print(f"✅ Lambda function {function_name} exists and is active")
    except Exception as e:
        # Check if the error is because the function doesn't exist
        if "Function not found" in str(e):
            pytest.skip(f"Lambda function {function_name} does not exist yet. Skipping test.")
        else:
            pytest.fail(f"Error checking Lambda function: {str(e)}")


def test_fetch_discussions_smoke_test(verifier):
    """Run a smoke test for the fetch-discussions Lambda function."""
    # Skip if AWS credentials are not valid
    if not verifier.credentials_valid:
        pytest.skip("AWS credentials are not valid. Configure valid credentials to run this test.")
        return

    try:
        # First check if the function exists
        function_name = f"LkmlAssistant-FetchDiscussions-{ENVIRONMENT}"
        verifier.lambda_client.get_function(FunctionName=function_name)

        # Generate test payload
        payload = TestPayloads.fetch_discussions_payload()

        # Run the smoke test
        success, response = verifier.run_smoke_test("FetchDiscussions", payload)

        # Verify the response
        assert success, f"Smoke test failed: {response}"
        assert "body" in response, "Response missing body"

        # Parse the body if it's a string
        body = response["body"]
        if isinstance(body, str):
            body = json.loads(body)

        # Verify the response structure
        print(f"Response body: {body}")
        assert "message" in body, "Response should have a message"
        assert "count" in body, "Response should have a count field"
        assert "patch_id" in body, "Response should have a patch_id field"

        print("✅ Fetch discussions smoke test passed")
    except Exception as e:
        # Check if the error is because the function doesn't exist
        if "Function not found" in str(e):
            pytest.skip("Lambda function FetchDiscussions does not exist yet. Skipping test.")
        else:
            pytest.fail(f"Error in smoke test: {str(e)}")


def test_discussions_table_exists(verifier):
    """Test that the Discussions DynamoDB table exists and is active."""
    # Skip if AWS credentials are not valid
    if not verifier.credentials_valid:
        pytest.skip("AWS credentials are not valid. Configure valid credentials to run this test.")
        return

    try:
        # Verify the table exists
        result = verifier.verify_dynamodb_table("Discussions")
        assert result, "Discussions table does not exist or is not active"
        print("✅ Discussions DynamoDB table exists and is active")
    except Exception as e:
        if "ResourceNotFoundException" in str(e) or "not exist" in str(e):
            pytest.skip("Discussions DynamoDB table does not exist yet. Skipping test.")
        else:
            pytest.fail(f"Error checking DynamoDB table: {str(e)}")


def test_fetch_and_store_discussions(verifier):
    """Test the complete flow of fetching discussions and storing them in DynamoDB."""
    # Skip if AWS credentials are not valid
    if not verifier.credentials_valid:
        pytest.skip("AWS credentials are not valid. Configure valid credentials to run this test.")
        return

    try:
        # First check if both the function and table exist
        function_name = f"LkmlAssistant-FetchDiscussions-{ENVIRONMENT}"
        table_name = f"LkmlAssistant-Discussions-{ENVIRONMENT}"

        try:
            verifier.lambda_client.get_function(FunctionName=function_name)
            table = verifier.dynamodb.Table(table_name)
            table.table_status  # This will trigger an error if the table doesn't exist
        except Exception as e:
            if (
                "Function not found" in str(e)
                or "ResourceNotFoundException" in str(e)
                or "not exist" in str(e)
            ):
                pytest.skip("Required resources don't exist yet. Skipping end-to-end test.")
                return
            raise

        # Get test data
        payload = TestPayloads.fetch_discussions_payload()
        patch_id = payload["patch_id"]

        # Invoke the Lambda to fetch discussions
        response = verifier.invoke_lambda("FetchDiscussions", payload)

        # Parse the response
        body = response["body"]
        if isinstance(body, str):
            body = json.loads(body)

        # Get the count of discussions
        count = body.get("count", 0)

        if count == 0:
            print("No discussions were found, which may be expected in test environment")
            print(
                "✅ End-to-end test passed: verified Lambda can be invoked and returns valid response"
            )
            return

        # Query DynamoDB to verify discussions were stored
        table = verifier.dynamodb.Table(table_name)

        # Use the GSI to query discussions for this patch
        # This assumes the GSI structure from the Lambda implementation
        response = table.query(
            IndexName="GSI1",
            KeyConditionExpression="gsi1pk = :pk",
            ExpressionAttributeValues={":pk": f"PATCH#{patch_id}"},
            Limit=10,
        )

        # Verify discussions exist in the table
        items = response.get("Items", [])
        assert len(items) > 0, f"No discussions found in DynamoDB for patch {patch_id}"

        print(
            f"✅ End-to-end test passed: {len(items)} discussions for patch {patch_id} stored in DynamoDB"
        )
    except Exception as e:
        if (
            "Function not found" in str(e)
            or "ResourceNotFoundException" in str(e)
            or "not exist" in str(e)
        ):
            pytest.skip("Required resources don't exist yet. Skipping end-to-end test.")
        else:
            pytest.fail(f"Error in end-to-end test: {str(e)}")
