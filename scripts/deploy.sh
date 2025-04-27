#!/bin/bash

# Script to deploy the LKML Assistant infrastructure
set -e

# Detect script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")
INFRA_DIR="$PROJECT_ROOT/infra"

# Default environment and stack name
ENV=${ENV:-"dev"}
STACK_NAME="LkmlAssistantStack-${ENV}"

# Define environment-specific settings
case $ENV in
  "dev")
    DEPLOY_FLAGS="--require-approval never"
    AWS_PROFILE=${AWS_PROFILE:-"default"}
    ;;
  "staging")
    DEPLOY_FLAGS="--require-approval any-change"
    AWS_PROFILE=${AWS_PROFILE:-"staging"}
    ;;
  "prod")
    DEPLOY_FLAGS="--require-approval any-change"
    AWS_PROFILE=${AWS_PROFILE:-"production"}
    # Require approval for production (skip prompt in CI environment)
    if [[ -z "$CI" ]]; then
      read -p "Are you sure you want to deploy to production? (y/n) " -n 1 -r
      echo
      if [[ ! $REPLY =~ ^[Yy]$ ]]
      then
        echo "Deployment cancelled"
        exit 1
      fi
    fi
    ;;
  *)
    echo "Unknown environment: $ENV"
    exit 1
    ;;
esac

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

check_dependencies() {
  log_info "Checking dependencies..."
  
  # Check for AWS CLI
  if ! command -v aws &> /dev/null; then
    log_error "AWS CLI is not installed. Please install it first."
    exit 1
  fi
  
  # Check for Node.js
  if ! command -v node &> /dev/null; then
    log_error "Node.js is not installed. Please install it first."
    exit 1
  fi
  
  # Check for CDK
  if ! command -v cdk &> /dev/null; then
    log_error "AWS CDK is not installed. Please install it by running: npm install -g aws-cdk"
    exit 1
  fi
  
  log_success "All dependencies are installed."
}

install_dependencies() {
  log_info "Installing dependencies..."
  
  # Install npm dependencies
  cd "$INFRA_DIR"
  npm install
  
  # Install Python dependencies
  cd "$PROJECT_ROOT"
  pip install -r requirements.txt
  
  log_success "Dependencies installed successfully."
}

build_code() {
  log_info "Building code..."
  
  # Build CDK code
  cd "$INFRA_DIR"
  npm run build
  
  log_success "Build completed successfully."
}

deploy_stack() {
  log_info "Deploying stack $STACK_NAME to $ENV environment..."
  
  # Deploy using CDK
  cd "$INFRA_DIR"
  
  # Bootstrap if needed
  log_info "Running bootstrap for $ENV environment..."
  # Use global CDK in CI environment if available, otherwise use local version
  if [[ -n "$CI" && -x "$(command -v cdk)" ]]; then
    # In CI environment with global CDK, use it directly
    log_info "Using global CDK for bootstrap"
    cdk bootstrap
  elif [ ! -z "$AWS_PROFILE" ]; then
    AWS_PROFILE=$AWS_PROFILE npm run bootstrap
  else
    npm run bootstrap
  fi
  
  # Deploy with environment-specific parameters
  log_info "Deploying with flags: $DEPLOY_FLAGS"
  if [[ -n "$CI" && -x "$(command -v cdk)" ]]; then
    # In CI environment with global CDK, use it directly
    log_info "Using global CDK for deployment"
    cdk deploy -c environment=$ENV $DEPLOY_FLAGS
  elif [ ! -z "$AWS_PROFILE" ]; then
    AWS_PROFILE=$AWS_PROFILE npm run deploy -- -c environment=$ENV $DEPLOY_FLAGS
  else
    npm run deploy -- -c environment=$ENV $DEPLOY_FLAGS
  fi
  
  log_success "Deployment completed successfully."
}

# Main execution
main() {
  log_info "Deploying LKML Assistant to $ENV environment"
  
  check_dependencies
  install_dependencies
  build_code
  deploy_stack
  
  log_success "LKML Assistant deployed successfully to $ENV environment!"
}

# Execute main function
main "$@"