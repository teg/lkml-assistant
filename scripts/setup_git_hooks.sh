#!/bin/bash

# Script to set up Git hooks for the project
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Setting up Git hooks for the project...${NC}"

# Create hooks directory if it doesn't exist
mkdir -p "$HOOKS_DIR"

# Create pre-commit hook
cat > "$HOOKS_DIR/pre-commit" << 'EOF'
#!/bin/bash

# Pre-commit hook to format all code in the project
echo "Running code autoformatting before commit..."

# Path to the format_all.sh script
FORMAT_SCRIPT="./scripts/format_all.sh"

# Check if the format script exists
if [ ! -f "$FORMAT_SCRIPT" ]; then
  echo "Error: Format script not found at $FORMAT_SCRIPT"
  exit 1
fi

# Make script executable if it isn't already
chmod +x "$FORMAT_SCRIPT"

# Run the formatting script
"$FORMAT_SCRIPT"

# Check if there are any changes after formatting
if git diff --quiet; then
  # No changes, we're good to go
  echo "✅ Code is properly formatted."
  exit 0
else
  # There are changes after formatting
  echo "🔄 Code was automatically reformatted. Please add the changes and commit again."
  exit 1
fi
EOF

# Make pre-commit hook executable
chmod +x "$HOOKS_DIR/pre-commit"

echo -e "${GREEN}Git hooks set up successfully!${NC}"
echo -e "${YELLOW}The pre-commit hook will now automatically format code before each commit.${NC}"