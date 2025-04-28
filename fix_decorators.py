#!/usr/bin/env python3
"""
Script to fix blank lines after function decorators.
E304: blank lines found after function decorator
"""

import re
import sys
import os
from pathlib import Path

def fix_file(file_path):
    """Fix decorator spacing issues in the given file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix decorator spacing - this pattern looks for a decorator followed by one or more blank lines
    # and replaces it with the decorator followed by a single newline
    fixed_content = re.sub(r'(@[\w_.]+[\(\)0-9a-zA-Z\'\",=\s]*)\n\s*\n+', r'\1\n', content)
    
    # Only write if changes were made
    if fixed_content != content:
        with open(file_path, 'w') as f:
            f.write(fixed_content)
        print(f"Fixed {file_path}")

def main():
    """Fix decorator spacing issues in Python files."""
    file_paths = [
        "src/utils/api.py",
        "src/utils/dynamodb.py",
        "src/utils/patchwork_api.py",
        "tests/integration/conftest.py"
    ]
    
    for file_path in file_paths:
        fix_file(file_path)

if __name__ == "__main__":
    main()