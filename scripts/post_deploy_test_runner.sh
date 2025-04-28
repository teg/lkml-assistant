#!/bin/bash

# Script to run post-deployment tests against a specific environment
# Usage: ./scripts/post_deploy_test_runner.sh [dev|staging|prod]

# Set default environment if not provided
ENVIRONMENT=${1:-dev}
VALID_ENVIRONMENTS=("dev" "staging" "prod")

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Detect script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

# Validate environment
valid_env=false
for env in "${VALID_ENVIRONMENTS[@]}"; do
  if [ "$ENVIRONMENT" == "$env" ]; then
    valid_env=true
    break
  fi
done

if [ "$valid_env" = false ]; then
  echo -e "${RED}Error: Invalid environment '${ENVIRONMENT}'. Must be one of: ${VALID_ENVIRONMENTS[*]}${NC}"
  exit 1
fi

# Check if running against production
if [ "$ENVIRONMENT" == "prod" ]; then
  echo -e "${YELLOW}Warning: You are about to run tests against the PRODUCTION environment.${NC}"
  read -p "Are you sure you want to continue? (y/N) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Test run cancelled.${NC}"
    exit 0
  fi
fi

echo -e "${BLUE}Running post-deployment tests for ${ENVIRONMENT} environment...${NC}"

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

# Run the post-deployment tests
echo -e "${BLUE}Executing tests against ${ENVIRONMENT} environment...${NC}"

# Check if AWS_PROFILE is set
if [ -n "$AWS_PROFILE" ]; then
  echo -e "${BLUE}Using AWS profile: ${AWS_PROFILE}${NC}"
  AWS_CMD_PROFILE="--profile $AWS_PROFILE"
else
  AWS_CMD_PROFILE=""
fi

cd "${PROJECT_ROOT}"
python -m tests.post_deploy.runner --env "$ENVIRONMENT" --verbose ${AWS_CMD_PROFILE:+--profile "$AWS_PROFILE"}

# Check the exit code
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
  echo -e "${GREEN}All post-deployment tests passed!${NC}"
else
  echo -e "${RED}Post-deployment tests failed with exit code ${EXIT_CODE}${NC}"
fi

# Deactivate virtual environment
deactivate

exit $EXIT_CODE