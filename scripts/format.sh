#!/bin/bash

# Script to format all Python code with Black

# Detect script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Formatting Python code with Black...${NC}"

cd "$PROJECT_ROOT"
black src tests

echo -e "${GREEN}Formatting complete!${NC}"