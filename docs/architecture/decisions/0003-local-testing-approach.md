# 3. Local Testing Approach for AWS Lambda Functions

Date: 2025-04-28

## Status

Accepted

## Context

The LKML Assistant application needs thorough testing strategies that allow for:

1. Fast and reliable validation of code changes
2. Testing AWS-integrated functionality without requiring actual AWS resources
3. Consistent code style and quality across the codebase
4. Flexibility to run tests in different environments (local development, CI/CD)

The traditional approach using LocalStack for testing AWS services works well but has some limitations:
- It requires running multiple containers
- Container networking can be challenging, especially on different platforms (macOS with Podman)
- Some AWS services aren't fully emulated in LocalStack
- Setup time for the test environment can be significant

## Decision

We have implemented a multi-faceted approach to local testing with the following components:

1. **Direct Lambda Invocation**: 
   - Invoke Lambda function code directly without using LocalStack
   - Mock AWS service clients to interact with local infrastructure
   - Support test mode with mock data

2. **Container-Based Testing**:
   - Use Docker/Podman for local service dependencies (primarily DynamoDB)
   - Containerize only the necessary services for specific test scenarios

3. **Flexible Test Runners**:
   - Separate scripts for different testing scenarios:
     - `run_tests.sh`: Main test runner that includes all essential checks
     - `run_direct_lambda_tests.sh`: Tests Lambda functions using direct invocation
     - `run_local_tests.sh`: Tests using LocalStack (when full AWS emulation is needed)

4. **Code Quality Tools**:
   - Flake8 for linting
   - Black for code formatting
   - Unit tests with pytest for core logic
   - Coverage reporting

5. **Make Targets**:
   - Simple, standardized commands for developers
   - `make test`: Run all tests
   - `make test-unit`: Run unit tests only
   - `make test-lambda-direct`: Run direct Lambda invocation tests
   - `make test-lambda-localstack`: Run LocalStack Lambda tests
   - `make format`: Format all Python code with Black

## Consequences

### Positive

1. **Faster Test Execution**:
   - Direct Lambda invocation tests are significantly faster than LocalStack tests
   - Developer feedback cycles are shortened

2. **Simplified Environment Setup**:
   - Reduced dependency on complex container networking
   - Only need DynamoDB container for many tests

3. **Better Test Coverage**:
   - More focused test scenarios
   - Easier to write tests that target specific functionality

4. **Platform Independence**:
   - Works with both Docker and Podman
   - Compatible with macOS, Linux, and potentially Windows

5. **Consistent Code Style**:
   - Automated formatting with Black
   - Style checks as part of the standard test flow
   - Same checks in CI/CD as in local development

### Negative

1. **Multiple Testing Approaches**:
   - More complexity in the testing infrastructure
   - Developers need to understand multiple approaches

2. **Mocked AWS Services**:
   - Direct invocation uses mocks, which might not perfectly match AWS behavior
   - Some edge cases might be missed

3. **Maintenance Overhead**:
   - Need to maintain multiple test scripts
   - Additional setup code for mocking

## Implementation Details

1. **Direct Lambda Invocation Mechanism**:
   - Mocks AWS service clients (like DynamoDB, Lambda)
   - Injects environment variables for test configuration
   - Directly calls Lambda handler functions with test events

2. **Container Management**:
   - Scripts handle container startup/cleanup
   - Proper error handling for existing containers
   - Compatible with Podman on macOS

3. **Code Quality Workflow**:
   - Black formatter checks during testing
   - Convenient `make format` command for developers
   - CI integration ensures consistent formatting

## Alternatives Considered

1. **Full LocalStack for Everything**:
   - Pro: Full AWS service emulation
   - Con: Slow, complex setup, platform compatibility issues

2. **Real AWS Resources for Testing**:
   - Pro: Tests against actual AWS behavior
   - Con: Cost, speed, infrastructure requirements

3. **Mocked Unit Tests Only**:
   - Pro: Fast, no infrastructure required
   - Con: Less realistic, misses integration issues

4. **Separate Testing Frameworks**:
   - Pro: Tailored to specific needs
   - Con: Inconsistent developer experience, learning curve