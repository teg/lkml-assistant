"""
Post-Deployment Verifier Utility

This module provides utilities for verifying AWS resources after deployment
and testing deployed Lambda functions with real AWS services.
"""

import json
import time
import os
import boto3
import logging
from typing import Dict, Any, Optional, List, Tuple
from botocore.config import Config
from botocore import UNSIGNED

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("post_deploy_verifier")


class DeploymentVerifier:
    """Utility class for verifying deployed AWS resources."""

    def __init__(
        self,
        environment: str = "dev",
        region: str = "us-east-1",
        profile: Optional[str] = None,
    ):
        """
        Initialize the deployment verifier.

        Args:
            environment: The deployment environment (dev, staging, prod)
            region: AWS region
            profile: AWS profile to use (optional)
        """
        self.environment = environment
        self.region = region
        self.profile = profile
        self.credentials_valid = False

        try:
            # Initialize boto3 session
            if profile:
                logger.info(f"Using AWS profile: {profile}")
                # Try multiple methods to ensure profile is used
                os.environ["AWS_PROFILE"] = profile
                os.environ["AWS_DEFAULT_PROFILE"] = profile

                self.session = boto3.Session(profile_name=profile, region_name=region)
            else:
                logger.info("No AWS profile specified, using default credentials")
                self.session = boto3.Session(region_name=region)

            # Log the effective credentials for debugging
            creds = self.session.get_credentials()
            if creds:
                logger.info(f"Using credentials for: {creds.access_key}")

            # Test credentials
            sts_client = self.session.client("sts")
            identity = sts_client.get_caller_identity()
            logger.info(f"AWS Identity: {identity.get('Arn')}")

            # Credentials are valid, initialize clients
            self.lambda_client = self.session.client("lambda")
            self.dynamodb = self.session.resource("dynamodb")
            self.logs_client = self.session.client("logs")

            # Resource naming prefix based on environment
            self.resource_prefix = f"LkmlAssistant-{environment}"

            self.credentials_valid = True
            logger.info(
                f"Initialized deployment verifier for {environment} environment in {region}"
            )
        except Exception as e:
            logger.warning(f"Failed to initialize AWS clients: {str(e)}")
            logger.warning(
                "Most tests will be skipped. To run post-deployment tests, configure valid AWS credentials."
            )
            # Create dummy clients for code to work, but operations will be skipped
            self.session = boto3.Session(region_name=region)
            self.lambda_client = self.session.client(
                "lambda", config=boto3.session.Config(signature_version=UNSIGNED)
            )
            self.dynamodb = self.session.resource("dynamodb")
            self.logs_client = self.session.client("logs")
            self.resource_prefix = f"LkmlAssistant-{environment}"

    def invoke_lambda(self, function_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke a Lambda function and return the response.

        Args:
            function_name: Base name of the Lambda function (without environment)
            payload: Event payload for the Lambda function

        Returns:
            Lambda function response
        """
        # Skip if credentials are invalid
        if not self.credentials_valid:
            logger.warning("Skipping Lambda invocation due to invalid credentials")
            raise ValueError(
                "AWS credentials are not valid. Configure valid credentials to run this test."
            )

        # Construct full function name with environment
        full_function_name = f"LkmlAssistant-{function_name}-{self.environment}"

        logger.info(f"Invoking Lambda function: {full_function_name}")
        response = self.lambda_client.invoke(
            FunctionName=full_function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload),
        )

        # Parse and return response
        response_payload = json.loads(response["Payload"].read().decode("utf-8"))
        logger.info(f"Lambda response status: {response['StatusCode']}")

        # Check for function errors
        if "FunctionError" in response:
            logger.error(f"Lambda function error: {response['FunctionError']}")
            logger.error(f"Error details: {response_payload}")
            raise Exception(f"Lambda function error: {response_payload}")

        return response_payload

    def verify_dynamodb_table(self, table_name: str) -> bool:
        """
        Verify that a DynamoDB table exists and is active.

        Args:
            table_name: Base name of the table (without environment)

        Returns:
            True if table exists and is active
        """
        # Skip if credentials are invalid
        if not self.credentials_valid:
            logger.warning("Skipping DynamoDB table verification due to invalid credentials")
            raise ValueError(
                "AWS credentials are not valid. Configure valid credentials to run this test."
            )

        # Construct full table name with environment
        full_table_name = f"LkmlAssistant-{table_name}-{self.environment}"

        try:
            table = self.dynamodb.Table(full_table_name)
            response = table.meta.client.describe_table(TableName=full_table_name)
            status = response["Table"]["TableStatus"]

            logger.info(f"DynamoDB table {full_table_name} exists with status: {status}")
            return status == "ACTIVE"
        except Exception as e:
            logger.error(f"Error verifying DynamoDB table {full_table_name}: {str(e)}")
            return False

    def get_lambda_logs(
        self,
        function_name: str,
        start_time: Optional[int] = None,
        duration_ms: int = 10000,
    ) -> List[Dict[str, Any]]:
        """
        Get recent CloudWatch logs for a Lambda function.

        Args:
            function_name: Base name of the Lambda function (without environment)
            start_time: Start time in milliseconds since epoch (optional)
            duration_ms: Duration to look back in milliseconds

        Returns:
            List of log events
        """
        # Skip if credentials are invalid
        if not self.credentials_valid:
            logger.warning("Skipping CloudWatch logs retrieval due to invalid credentials")
            raise ValueError(
                "AWS credentials are not valid. Configure valid credentials to run this test."
            )

        # Construct full function name with environment
        full_function_name = f"LkmlAssistant-{function_name}-{self.environment}"
        log_group_name = f"/aws/lambda/{full_function_name}"

        # Calculate start and end times
        end_time = int(time.time() * 1000)
        if start_time is None:
            start_time = end_time - duration_ms

        try:
            # Get log streams
            streams_response = self.logs_client.describe_log_streams(
                logGroupName=log_group_name,
                orderBy="LastEventTime",
                descending=True,
                limit=5,
            )

            all_events = []

            # Get log events from each stream
            for stream in streams_response.get("logStreams", []):
                stream_name = stream["logStreamName"]
                events_response = self.logs_client.get_log_events(
                    logGroupName=log_group_name,
                    logStreamName=stream_name,
                    startTime=start_time,
                    endTime=end_time,
                    limit=100,
                )

                all_events.extend(events_response.get("events", []))

            logger.info(f"Retrieved {len(all_events)} log events for {full_function_name}")
            return all_events

        except Exception as e:
            logger.error(f"Error getting logs for {full_function_name}: {str(e)}")
            return []

    def run_smoke_test(
        self, function_name: str, payload: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Run a smoke test for a Lambda function.

        Args:
            function_name: Base name of the Lambda function (without environment)
            payload: Test payload

        Returns:
            Tuple of (success, response)
        """
        # Skip if credentials are invalid
        if not self.credentials_valid:
            logger.warning("Skipping smoke test due to invalid credentials")
            raise ValueError(
                "AWS credentials are not valid. Configure valid credentials to run this test."
            )

        try:
            # Record start time for logs
            start_time = int(time.time() * 1000)

            # Invoke Lambda function
            response = self.invoke_lambda(function_name, payload)

            # Check for successful response
            if "statusCode" in response and response["statusCode"] in (
                200,
                201,
                202,
                204,
            ):
                logger.info(f"Smoke test passed for {function_name}")
                return True, response
            else:
                logger.warning(
                    f"Smoke test failed for {function_name}: Unexpected response: {response}"
                )

                # Get logs for debugging
                time.sleep(5)  # Wait for logs to be available
                logs = self.get_lambda_logs(function_name, start_time)
                logger.info(f"Recent logs: {logs}")

                return False, response

        except Exception as e:
            logger.error(f"Smoke test failed for {function_name} with error: {str(e)}")
            return False, {"error": str(e)}


# Test payload generators for common Lambda functions
class TestPayloads:
    """Standard test payloads for different Lambda functions."""

    @staticmethod
    def fetch_patches_payload(limit: int = 5) -> Dict[str, Any]:
        """Generate a test payload for the fetch-patches Lambda."""
        return {"limit": limit, "test_mode": True}

    @staticmethod
    def fetch_discussions_payload(
        patch_id: str = "test-patch-id", message_id: str = "test-message-id"
    ) -> Dict[str, Any]:
        """Generate a test payload for the fetch-discussions Lambda."""
        return {"patch_id": patch_id, "message_id": message_id, "test_mode": True}

    @staticmethod
    def refresh_discussions_payload(
        days_to_look_back: int = 7, limit: int = 5, test_mode: bool = True
    ) -> Dict[str, Any]:
        """Generate a test payload for the refresh-discussions Lambda."""
        return {
            "days_to_look_back": days_to_look_back,
            "limit": limit,
            "source": "test",
            "test_mode": test_mode,
        }

    @staticmethod
    def process_discussions_payload(patch_id: str = "test-patch-id") -> Dict[str, Any]:
        """Generate a test payload for the process-discussions Lambda."""
        return {"patchId": patch_id, "test_mode": True}
