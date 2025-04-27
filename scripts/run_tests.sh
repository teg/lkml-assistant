#!/bin/bash

# Script to run all tests for the LKML Assistant application
set -e

# Detect script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
  echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

# Run Python linting
run_python_lint() {
  log_info "Running Python linting..."
  
  cd "$PROJECT_ROOT"
  flake8 src tests
  
  if [ $? -eq 0 ]; then
    log_success "Python linting passed"
    return 0
  else
    log_error "Python linting failed"
    return 1
  fi
}

# Run Python unit tests
run_python_unit_tests() {
  log_info "Running Python unit tests..."
  
  cd "$PROJECT_ROOT"
  python -m pytest tests/unit -v
  
  if [ $? -eq 0 ]; then
    log_success "Python unit tests passed"
    return 0
  else
    log_error "Python unit tests failed"
    return 1
  fi
}

# Run Python integration tests
run_python_integration_tests() {
  log_info "Running Python integration tests..."
  
  cd "$PROJECT_ROOT"
  python -m pytest tests/integration -v
  
  if [ $? -eq 0 ]; then
    log_success "Python integration tests passed"
    return 0
  else
    log_error "Python integration tests failed"
    return 1
  fi
}

# Run TypeScript linting
run_typescript_lint() {
  log_info "Running TypeScript linting..."
  
  cd "$PROJECT_ROOT/infra"
  npm run lint
  
  if [ $? -eq 0 ]; then
    log_success "TypeScript linting passed"
    return 0
  else
    log_error "TypeScript linting failed"
    return 1
  fi
}

# Run TypeScript tests
run_typescript_tests() {
  log_info "Running TypeScript tests..."
  
  cd "$PROJECT_ROOT/infra"
  npm test
  
  if [ $? -eq 0 ]; then
    log_success "TypeScript tests passed"
    return 0
  else
    log_error "TypeScript tests failed"
    return 1
  fi
}

# Run CDK synth to verify infrastructure
run_cdk_synth() {
  log_info "Running CDK synthesis..."
  
  cd "$PROJECT_ROOT/infra"
  npm run synth
  
  if [ $? -eq 0 ]; then
    log_success "CDK synthesis passed"
    return 0
  else
    log_error "CDK synthesis failed"
    return 1
  fi
}

# Main function to run all tests
run_all_tests() {
  log_info "Running all tests..."
  
  local failures=0
  
  # Run Python tests
  run_python_lint
  failures=$((failures + $?))
  
  run_python_unit_tests
  failures=$((failures + $?))
  
  run_python_integration_tests
  failures=$((failures + $?))
  
  # Run TypeScript tests
  run_typescript_lint
  failures=$((failures + $?))
  
  run_typescript_tests
  failures=$((failures + $?))
  
  # Verify infrastructure
  run_cdk_synth
  failures=$((failures + $?))
  
  # Report results
  if [ $failures -eq 0 ]; then
    log_success "All tests passed successfully!"
    return 0
  else
    log_error "Tests completed with $failures failures"
    return 1
  fi
}

# Run specific test suite if provided, otherwise run all
if [ $# -eq 0 ]; then
  run_all_tests
else
  case "$1" in
    "python-lint") run_python_lint ;;
    "python-unit") run_python_unit_tests ;;
    "python-integration") run_python_integration_tests ;;
    "typescript-lint") run_typescript_lint ;;
    "typescript-tests") run_typescript_tests ;;
    "cdk-synth") run_cdk_synth ;;
    *)
      log_error "Unknown test suite: $1"
      echo "Available test suites:"
      echo "  python-lint         - Run Python linting"
      echo "  python-unit         - Run Python unit tests"
      echo "  python-integration  - Run Python integration tests"
      echo "  typescript-lint     - Run TypeScript linting"
      echo "  typescript-tests    - Run TypeScript tests"
      echo "  cdk-synth           - Verify CDK infrastructure"
      echo ""
      echo "  [no arguments]      - Run all tests"
      exit 1
      ;;
  esac
fi