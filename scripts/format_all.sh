#!/bin/bash

# Script to format all code in the project (Python and TypeScript)
# Focus on autoformatting only - no linting

# Detect script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Change to project root
cd "$PROJECT_ROOT"

# Format Python code with Black
echo -e "${BLUE}Formatting Python code with Black...${NC}"
black src tests

# Format TypeScript code with Prettier
echo -e "${BLUE}Formatting TypeScript code with Prettier...${NC}"
if [ -d "infra" ]; then
  cd infra
  if [ -f "package.json" ] && grep -q "\"format\"" package.json; then
    npm run format
  else
    echo -e "${YELLOW}No format script found in package.json. Skipping TypeScript formatting.${NC}"
  fi
  cd "$PROJECT_ROOT"
else
  echo -e "${YELLOW}No infra directory found. Skipping TypeScript formatting.${NC}"
fi

echo -e "${GREEN}Formatting complete!${NC}"