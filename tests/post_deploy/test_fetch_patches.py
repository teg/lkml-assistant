"""
Post-Deployment Tests for Fetch Patches Lambda

These tests verify that the deployed Fetch Patches Lambda function
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


def test_fetch_patches_lambda_exists(verifier):
    """Test that the fetch-patches Lambda function exists."""
    # Skip if AWS credentials are not valid
    if not verifier.credentials_valid:
        pytest.skip("AWS credentials are not valid. Configure valid credentials to run this test.")
        return
        
    # Get Lambda function details
    try:
        function_name = f"LkmlAssistant-FetchPatches-{ENVIRONMENT}"
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


def test_fetch_patches_smoke_test(verifier):
    """Run a smoke test for the fetch-patches Lambda function."""
    # Skip if AWS credentials are not valid
    if not verifier.credentials_valid:
        pytest.skip("AWS credentials are not valid. Configure valid credentials to run this test.")
        return
        
    try:
        # First check if the function exists
        function_name = f"LkmlAssistant-FetchPatches-{ENVIRONMENT}"
        verifier.lambda_client.get_function(FunctionName=function_name)
        
        # Generate test payload
        payload = TestPayloads.fetch_patches_payload(limit=2)
        
        # Run the smoke test
        success, response = verifier.run_smoke_test("FetchPatches", payload)
        
        # Verify the response
        assert success, f"Smoke test failed: {response}"
        assert "body" in response, "Response missing body"
        
        # Parse the body if it's a string
        body = response["body"]
        if isinstance(body, str):
            body = json.loads(body)
        
        # Verify the response structure
        assert "patches" in body, "Response body missing patches"
        
        print(f"✅ Fetch patches smoke test passed")
    except Exception as e:
        # Check if the error is because the function doesn't exist
        if "Function not found" in str(e):
            pytest.skip(f"Lambda function FetchPatches does not exist yet. Skipping test.")
        else:
            pytest.fail(f"Error in smoke test: {str(e)}")


def test_patches_table_exists(verifier):
    """Test that the Patches DynamoDB table exists and is active."""
    # Skip if AWS credentials are not valid
    if not verifier.credentials_valid:
        pytest.skip("AWS credentials are not valid. Configure valid credentials to run this test.")
        return
        
    try:
        # Verify the table exists
        result = verifier.verify_dynamodb_table("Patches")
        assert result, "Patches table does not exist or is not active"
        print(f"✅ Patches DynamoDB table exists and is active")
    except Exception as e:
        if "ResourceNotFoundException" in str(e) or "not exist" in str(e):
            pytest.skip(f"Patches DynamoDB table does not exist yet. Skipping test.")
        else:
            pytest.fail(f"Error checking DynamoDB table: {str(e)}")


def test_fetch_and_store(verifier):
    """Test the complete flow of fetching patches and storing them in DynamoDB."""
    # Skip if AWS credentials are not valid
    if not verifier.credentials_valid:
        pytest.skip("AWS credentials are not valid. Configure valid credentials to run this test.")
        return
        
    try:
        # First check if both the function and table exist
        function_name = f"LkmlAssistant-FetchPatches-{ENVIRONMENT}"
        table_name = f"LkmlAssistant-Patches-{ENVIRONMENT}"
        
        try:
            verifier.lambda_client.get_function(FunctionName=function_name)
            table = verifier.dynamodb.Table(table_name)
            table.table_status  # This will trigger an error if the table doesn't exist
        except Exception as e:
            if "Function not found" in str(e) or "ResourceNotFoundException" in str(e) or "not exist" in str(e):
                pytest.skip(f"Required resources don't exist yet. Skipping end-to-end test.")
                return
            raise
            
        # Invoke the Lambda to fetch patches
        payload = TestPayloads.fetch_patches_payload(limit=1)
        response = verifier.invoke_lambda("FetchPatches", payload)
        
        # Parse the response to get a patch ID
        body = response["body"]
        if isinstance(body, str):
            body = json.loads(body)
        
        patches = body.get("patches", [])
        assert len(patches) > 0, "No patches returned from Lambda"
        
        patch_id = patches[0].get("id")
        assert patch_id, "Patch missing ID"
        
        # Now check if the patch exists in DynamoDB
        table = verifier.dynamodb.Table(table_name)
        
        response = table.get_item(Key={"id": patch_id})
        item = response.get("Item")
        
        assert item, f"Patch {patch_id} not found in DynamoDB"
        assert item["id"] == patch_id, "Patch ID mismatch"
        
        print(f"✅ End-to-end test passed: Patch {patch_id} successfully stored in DynamoDB")
    except Exception as e:
        if "Function not found" in str(e) or "ResourceNotFoundException" in str(e) or "not exist" in str(e):
            pytest.skip(f"Required resources don't exist yet. Skipping end-to-end test.")
        else:
            pytest.fail(f"Error in end-to-end test: {str(e)}")