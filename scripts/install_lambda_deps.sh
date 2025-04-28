#!/bin/bash

# Script to install Python dependencies for Lambda functions

# Set the project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create a temporary directory for Lambda layers
TEMP_DIR="$PROJECT_ROOT/temp"
mkdir -p "$TEMP_DIR"

echo -e "${BLUE}Installing Lambda dependencies${NC}"

# Find all requirements.txt files in Lambda function directories
LAMBDA_DIRS=$(find "$PROJECT_ROOT/src/functions" -type d -mindepth 1 -maxdepth 1)

for LAMBDA_DIR in $LAMBDA_DIRS; do
  LAMBDA_NAME=$(basename "$LAMBDA_DIR")
  REQUIREMENTS_FILE="$LAMBDA_DIR/requirements.txt"
  
  if [ -f "$REQUIREMENTS_FILE" ]; then
    echo -e "${BLUE}Installing dependencies for ${LAMBDA_NAME}...${NC}"
    
    # Create a directory for dependencies
    DEPS_DIR="$LAMBDA_DIR/python"
    mkdir -p "$DEPS_DIR"
    
    # Install dependencies to the python directory
    pip install -r "$REQUIREMENTS_FILE" --target "$DEPS_DIR" --upgrade
    
    echo -e "${GREEN}Successfully installed dependencies for ${LAMBDA_NAME}${NC}"
  else
    echo -e "${YELLOW}No requirements.txt found for ${LAMBDA_NAME}, skipping${NC}"
  fi
done

echo -e "${GREEN}All Lambda dependencies installed successfully${NC}"