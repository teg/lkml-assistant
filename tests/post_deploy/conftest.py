"""
PyTest configuration for post-deployment tests.
"""

import os
import pytest
import logging
from .post_deploy_verifier import DeploymentVerifier

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("post_deploy_tests")


def pytest_configure(config):
    """Configure PyTest for post-deployment tests."""
    # Add custom markers
    config.addinivalue_line("markers", "smoke: smoke tests for deployed resources")
    config.addinivalue_line(
        "markers", "integration: integration tests for deployed resources"
    )
    config.addinivalue_line(
        "markers", "configuration: tests for resource configuration"
    )


@pytest.fixture(scope="session")
def environment():
    """Get the test environment from environment variables."""
    env = os.environ.get("TEST_ENVIRONMENT", "dev")
    logger.info(f"Running tests against {env} environment")
    return env


@pytest.fixture(scope="session")
def aws_region():
    """Get the AWS region from environment variables."""
    return os.environ.get("AWS_REGION", "us-east-1")


@pytest.fixture(scope="session")
def aws_profile():
    """Get the AWS profile from environment variables."""
    return os.environ.get("AWS_PROFILE")


@pytest.fixture(scope="session")
def verifier(environment, aws_region, aws_profile):
    """Create a deployment verifier for tests."""
    return DeploymentVerifier(
        environment=environment, region=aws_region, profile=aws_profile
    )


@pytest.fixture
def lambda_function_name(environment):
    """Get the full Lambda function name for the environment."""

    def _get_function_name(base_name):
        return f"LkmlAssistant-{base_name}-{environment}"

    return _get_function_name


@pytest.fixture
def dynamodb_table_name(environment):
    """Get the full DynamoDB table name for the environment."""

    def _get_table_name(base_name):
        return f"LkmlAssistant-{base_name}-{environment}"

    return _get_table_name
