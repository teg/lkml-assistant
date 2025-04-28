#!/bin/bash

# Script to run post-deployment tests for a specific environment
# Usage: ./post_deploy_test_runner.sh [env] [options]

# Detect script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default environment is dev
ENV="dev"
# Default region
REGION="us-east-1"
# Default report directory
REPORT_DIR="test-reports"
# Default verbosity
VERBOSE=false
# Default metrics reporting
NO_METRICS=false
# Default dry run mode
DRY_RUN=false
# Default test file (empty to run all)
TEST_FILE=""

# Parse arguments
if [ $# -gt 0 ]; then
  ENV="$1"
  shift
fi

# Parse remaining options
while [ $# -gt 0 ]; do
  case "$1" in
    --region)
      REGION="$2"
      shift 2
      ;;
    --profile)
      PROFILE="$2"
      shift 2
      ;;
    --report-dir)
      REPORT_DIR="$2"
      shift 2
      ;;
    --test-file)
      TEST_FILE="$2"
      shift 2
      ;;
    --verbose|-v)
      VERBOSE=true
      shift
      ;;
    --no-metrics)
      NO_METRICS=true
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      echo "Usage: $0 [env] [--region REGION] [--profile PROFILE] [--report-dir DIR] [--test-file FILE] [--verbose] [--no-metrics] [--dry-run]"
      exit 1
      ;;
  esac
done

# Validate environment
if [[ ! "$ENV" =~ ^(dev|staging|prod)$ ]]; then
  echo -e "${RED}Invalid environment: $ENV${NC}"
  echo "Environment must be one of: dev, staging, prod"
  exit 1
fi

# Confirm production tests
if [ "$ENV" == "prod" ]; then
  echo -e "${YELLOW}Warning: You are about to run tests against the PRODUCTION environment.${NC}"
  read -p "Are you sure you want to continue? (y/N) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Test run cancelled.${NC}"
    exit 0
  fi
fi

# Build arguments for the Python runner
ARGS=("--env" "$ENV" "--region" "$REGION")

if [ -n "$PROFILE" ]; then
  ARGS+=("--profile" "$PROFILE")
fi

if [ -n "$REPORT_DIR" ]; then
  ARGS+=("--report-dir" "$REPORT_DIR")
fi

if [ -n "$TEST_FILE" ]; then
  ARGS+=("--test-file" "$TEST_FILE")
fi

if [ "$VERBOSE" = true ]; then
  ARGS+=("--verbose")
fi

if [ "$NO_METRICS" = true ]; then
  ARGS+=("--no-metrics")
fi

if [ "$DRY_RUN" = true ]; then
  ARGS+=("--dry-run")
fi

# Run tests
echo -e "${BLUE}Running post-deployment tests for ${GREEN}$ENV${BLUE} environment...${NC}"
echo -e "${BLUE}Test results will be saved to: ${GREEN}$REPORT_DIR${NC}"

# Setup Python virtual environment if needed
if [ ! -d "${PROJECT_ROOT}/venv" ]; then
  echo -e "${BLUE}Creating Python virtual environment...${NC}"
  python3 -m venv "${PROJECT_ROOT}/venv"
fi

# Activate virtual environment
source "${PROJECT_ROOT}/venv/bin/activate"

# Install dependencies if needed
if ! pip show pytest > /dev/null 2>&1; then
  echo -e "${BLUE}Installing dependencies...${NC}"
  # Install main requirements first
  if [ -f "${PROJECT_ROOT}/requirements.txt" ]; then
    pip install -r "${PROJECT_ROOT}/requirements.txt"
  fi
  
  # Install additional dev requirements if they exist
  if [ -f "${PROJECT_ROOT}/requirements-dev.txt" ]; then
    pip install -r "${PROJECT_ROOT}/requirements-dev.txt"
  fi
  
  # Install pytest-html specifically if not included in requirements
  if ! pip show pytest-html > /dev/null 2>&1; then
    pip install pytest-html
  fi
fi

# Ensure the post-deployment test directory exists
if [ ! -d "${PROJECT_ROOT}/tests/post_deploy" ]; then
  echo -e "${RED}Error: Post-deployment test directory not found${NC}"
  exit 1
fi

# Ensure post-deployment test runner exists
if [ ! -f "${PROJECT_ROOT}/tests/post_deploy/runner.py" ]; then
  echo -e "${RED}Error: Post-deployment test runner script not found${NC}"
  exit 1
fi

# For more predictable Python environment
cd "$PROJECT_ROOT"

# Run the Python runner with the collected arguments
python -m tests.post_deploy.runner "${ARGS[@]}"
EXIT_CODE=$?

# Show test summary
LATEST_REPORT_DIR=$(find "$REPORT_DIR" -maxdepth 1 -name "${ENV}_*" -type d | sort -r | head -n 1)
if [ -n "$LATEST_REPORT_DIR" ] && [ -f "$LATEST_REPORT_DIR/summary.txt" ]; then
  echo ""
  echo -e "${BLUE}Test Summary:${NC}"
  cat "$LATEST_REPORT_DIR/summary.txt"
  echo ""
  echo -e "${BLUE}Full HTML report is available at: ${GREEN}$LATEST_REPORT_DIR/html-report.html${NC}"
else
  echo -e "${YELLOW}No test summary available${NC}"
fi

if [ $EXIT_CODE -eq 0 ]; then
  echo -e "${GREEN}Tests completed successfully!${NC}"
else
  echo -e "${RED}Tests failed with exit code $EXIT_CODE${NC}"
fi

# Deactivate virtual environment
deactivate

exit $EXIT_CODE