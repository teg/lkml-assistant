"""
Post-Deployment Tests for Refresh Discussions Lambda

These tests verify that the deployed Refresh Discussions Lambda function
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


def test_refresh_discussions_lambda_exists(verifier):
    """Test that the refresh-discussions Lambda function exists."""
    # Skip if AWS credentials are not valid
    if not verifier.credentials_valid:
        pytest.skip("AWS credentials are not valid. Configure valid credentials to run this test.")
        return

    # Get Lambda function details
    try:
        function_name = f"LkmlAssistant-RefreshDiscussions-{ENVIRONMENT}"
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


def test_refresh_discussions_smoke_test(verifier):
    """Run a smoke test for the refresh-discussions Lambda function."""
    # Skip if AWS credentials are not valid
    if not verifier.credentials_valid:
        pytest.skip("AWS credentials are not valid. Configure valid credentials to run this test.")
        return

    try:
        # First check if the function exists
        function_name = f"LkmlAssistant-RefreshDiscussions-{ENVIRONMENT}"
        verifier.lambda_client.get_function(FunctionName=function_name)

        # Generate test payload
        payload = TestPayloads.refresh_discussions_payload(limit=2)

        # Run the smoke test
        success, response = verifier.run_smoke_test("RefreshDiscussions", payload)

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
        assert "source" in body, "Response should have a source field"
        assert "success_count" in body, "Response should have a success_count field"
        assert "failure_count" in body, "Response should have a failure_count field"

        print("✅ Refresh discussions smoke test passed")
    except Exception as e:
        # Check if the error is because the function doesn't exist
        if "Function not found" in str(e):
            pytest.skip("Lambda function RefreshDiscussions does not exist yet. Skipping test.")
        else:
            pytest.fail(f"Error in smoke test: {str(e)}")


def test_refresh_discussions_end_to_end(verifier):
    """Test the complete flow of refreshing discussions for recent patches."""
    # Skip if AWS credentials are not valid
    if not verifier.credentials_valid:
        pytest.skip("AWS credentials are not valid. Configure valid credentials to run this test.")
        return

    try:
        # First check if the function exists
        function_name = f"LkmlAssistant-RefreshDiscussions-{ENVIRONMENT}"
        verifier.lambda_client.get_function(FunctionName=function_name)

        # Also check if the fetch-discussions function exists, as it's needed by refresh-discussions
        fetch_function_name = f"LkmlAssistant-FetchDiscussions-{ENVIRONMENT}"
        verifier.lambda_client.get_function(FunctionName=fetch_function_name)

        # Generate test payload with a small limit to make the test faster
        payload = TestPayloads.refresh_discussions_payload(
            days_to_look_back=1,  # Only look back 1 day
            limit=2,  # Process at most 2 patches
            test_mode=True,  # Enable test mode
        )

        # Invoke the Lambda to refresh discussions
        response = verifier.invoke_lambda("RefreshDiscussions", payload)

        # Parse the response
        body = response["body"]
        if isinstance(body, str):
            body = json.loads(body)

        # Check that the response has the expected fields
        assert "message" in body, "Response should have a message"
        assert "success_count" in body, "Response should have a success_count field"
        assert "failure_count" in body, "Response should have a failure_count field"
        assert "total_patches" in body, "Response should have a total_patches field"

        # For test mode, we expect the success and failure counts to be accurate
        total_patches = body.get("total_patches", 0)
        success_count = body.get("success_count", 0)
        failure_count = body.get("failure_count", 0)

        # The total should equal success + failure
        assert (
            total_patches == success_count + failure_count
        ), "Total patches should equal success + failure"

        print(
            f"✅ End-to-end test passed: RefreshDiscussions processed {total_patches} patches "
            f"({success_count} successful, {failure_count} failed)"
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
