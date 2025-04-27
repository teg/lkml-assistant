# Testing Guide

This document provides information about testing the LKML Assistant application.

## Running Tests

The project includes a comprehensive test suite with both unit and integration tests.

### Using Make Commands

The following Make commands are available for running tests:

```bash
# Run all tests
make test

# Run Python tests
make test-python

# Run TypeScript tests
make test-typescript

# Run only unit tests for Python code
make test-python-unit

# Run only integration tests for Python code
make test-python-integration

# Run linting checks
make lint

# Format code according to style guidelines
make fmt

# Run tests with coverage report
make coverage
```

### Using the Test Script Directly

You can also use the test script directly for more flexibility:

```bash
# Run all tests
./scripts/run_tests.sh

# Run specific test suites
./scripts/run_tests.sh python-lint
./scripts/run_tests.sh python-unit
./scripts/run_tests.sh python-integration
./scripts/run_tests.sh typescript-lint
./scripts/run_tests.sh typescript-tests
./scripts/run_tests.sh cdk-synth
```

## Test Organization

The tests are organized as follows:

### Unit Tests

- **Python Unit Tests**: Located in `tests/unit/`
  - `functions/`: Tests for Lambda functions
  - `utils/`: Tests for utility modules
  - `repositories/`: Tests for repository modules

- **TypeScript Unit Tests**: Located in `infra/test/`
  - Tests for CDK infrastructure

### Integration Tests

- **DynamoDB Integration Tests**: Located in `tests/integration/`
  - Tests that verify the interactions with DynamoDB using mock services

## Test Requirements

To run the tests, you need:

1. Python 3.9 or higher
2. Node.js 16 or higher
3. Python packages: pytest, moto, boto3, requests
4. Node.js packages: jest, ts-jest

All dependencies can be installed using:

```bash
make install-deps
```

## Continuous Integration

The project is configured with GitHub Actions for continuous integration:

1. **CI Workflow**: Runs on pull requests and pushes to main
   - Runs linting checks
   - Runs unit tests
   - Runs CDK synthesis

2. **Test Workflow**: Can be run manually
   - Runs all tests with coverage
   - Uploads coverage reports to Codecov

## Test Coverage

The test suite is configured to require a minimum of 80% test coverage for Python code and 70% for TypeScript code.

To view code coverage, run:

```bash
make coverage
```

This will generate an HTML report in the `htmlcov/` directory that you can open in a browser.

## Adding New Tests

When adding new functionality, please follow these guidelines:

1. Add unit tests for all new functions, classes, and modules
2. Ensure all error cases are tested
3. Add integration tests for complex interactions
4. Maintain or improve the current test coverage

## Mocking AWS Services

The integration tests use the `moto` library to mock AWS services like DynamoDB, Lambda, and SQS. This allows us to test interactions with these services without incurring AWS costs or requiring AWS credentials during testing.