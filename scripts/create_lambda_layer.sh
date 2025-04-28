#!/bin/bash

# Script to create a Lambda layer with Python dependencies

# Set the project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create a temporary directory for Lambda layer
LAYER_DIR="$PROJECT_ROOT/lambda_layer"
rm -rf "$LAYER_DIR"
mkdir -p "$LAYER_DIR/python"

echo -e "${BLUE}Creating Lambda layer with common dependencies${NC}"

# Combine all requirements files
COMBINED_REQUIREMENTS="$LAYER_DIR/requirements.txt"
echo "" > "$COMBINED_REQUIREMENTS"

# Use a temporary file to collect requirements
TMP_REQUIREMENTS=$(mktemp)
echo "" > "$TMP_REQUIREMENTS"

# Find all requirements.txt files in Lambda function directories
for REQUIREMENTS_FILE in $(find "$PROJECT_ROOT/src/functions" -name "requirements.txt"); do
  echo -e "${BLUE}Adding requirements from ${REQUIREMENTS_FILE}${NC}"
  cat "$REQUIREMENTS_FILE" >> "$TMP_REQUIREMENTS"
  echo "" >> "$TMP_REQUIREMENTS" # Add newline between files
done

# Remove duplicates and sort
cat "$TMP_REQUIREMENTS" | grep -v "^$" | sort -u > "$COMBINED_REQUIREMENTS"
rm "$TMP_REQUIREMENTS"

# Display the combined requirements
echo -e "${BLUE}Combined requirements:${NC}"
cat "$COMBINED_REQUIREMENTS"

echo -e "${BLUE}Installing dependencies to layer directory...${NC}"
pip install -r "$COMBINED_REQUIREMENTS" --target "$LAYER_DIR/python" --upgrade

# Create a zip file for the layer
cd "$LAYER_DIR"
zip -r ../lambda_layer.zip .

echo -e "${GREEN}Lambda layer created successfully at: ${PROJECT_ROOT}/lambda_layer.zip${NC}"