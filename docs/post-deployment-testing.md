# Post-Deployment Testing

This document describes the post-deployment testing approach for the LKML Community Guide project.

## Overview

Post-deployment testing verifies that the application works correctly in the actual AWS environment after deployment. These tests complement local and CI/CD tests by validating that:

1. AWS resources are correctly provisioned and configured
2. Lambda functions can be invoked and produce expected results
3. Data flows correctly through the deployed system
4. Integration with real AWS services works as expected

## Test Structure

Post-deployment tests are organized in the `tests/post_deploy` directory and follow these principles:

- Tests connect to real AWS resources in the target environment
- Test cases reuse logic from local tests when possible
- Tests are parameterized to support different environments (dev, staging, prod)
- Testing is automated through CI/CD but can also be run manually

## Running Post-Deployment Tests

### Prerequisites

- AWS credentials with appropriate permissions
- Python 3.9+
- Project dependencies installed (`pip install -r requirements.txt -r requirements-dev.txt`)

### Using Make Commands

The project provides Make targets for running post-deployment tests:

```bash
# Test against development environment
make test-post-deploy-dev

# Test against staging environment
make test-post-deploy-staging

# Test against production environment
make test-post-deploy-prod

# Default (same as test-post-deploy-dev)
make test-post-deploy
```

### Using the Test Runner Script

You can also use the test runner script directly:

```bash
# Basic usage with default parameters
./scripts/post_deploy_test_runner.sh dev

# Passing additional parameters
python -m tests.post_deploy.runner --env staging --verbose --test-file tests/post_deploy/test_fetch_patches.py
```

## Types of Post-Deployment Tests

### Smoke Tests

Smoke tests verify that the basic functionality works by:
- Confirming AWS resources exist and are properly configured
- Invoking Lambda functions with simple payloads
- Checking that DynamoDB tables are accessible and have the expected schema

### Integration Tests

Integration tests verify that different components work together by:
- Testing end-to-end workflows across multiple services
- Verifying data consistency between components
- Checking that event-driven processing works correctly

### Configuration Tests

Configuration tests verify that resources are correctly configured by:
- Checking IAM permissions and roles
- Verifying environment variables and configuration
- Confirming resource limits and scaling settings

## CI/CD Integration

Post-deployment tests are integrated into the CI/CD pipeline through the `.github/workflows/post-deploy-verify.yml` workflow, which:

1. Automatically runs after successful deployments to the `main` branch
2. Can be manually triggered for any environment
3. Reports test results and notifications for failures
4. Creates issues for failed tests that require attention

## Best Practices

When writing post-deployment tests:

1. **Focus on verification, not exploration**: Tests should verify expected behavior, not explore the system.
2. **Keep tests fast and reliable**: Avoid long-running tests or tests with external dependencies.
3. **Clean up test data**: Tests should clean up any data they create to avoid polluting the environment.
4. **Use proper assertions**: Tests should clearly assert the expected conditions.
5. **Handle AWS rate limits**: Add retries and backoff for AWS operations that might be rate-limited.
6. **Respect environment levels**: Be careful when testing against production environments.

## Extending Test Coverage

To add tests for new features:

1. Create a new test module in `tests/post_deploy/`
2. Use the `DeploymentVerifier` utility for AWS interactions
3. Create test payload generators for the new Lambda functions
4. Add smoke tests for basic functionality
5. Add integration tests for end-to-end flows
6. Update documentation as needed