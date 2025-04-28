#!/usr/bin/env python3
"""
Script to fix common linting issues:
- Remove trailing whitespace
- Add newlines at end of files
- Fix blank lines with whitespace
- Ensure proper spacing between functions
"""

import os
import re
import sys
from pathlib import Path

def fix_file(file_path):
    """Fix linting issues in the given file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix trailing whitespace on lines
    content = re.sub(r'[ \t]+$', '', content, flags=re.MULTILINE)
    
    # Fix blank lines with whitespace
    content = re.sub(r'^[ \t]+$', '', content, flags=re.MULTILINE)
    
    # Ensure file ends with a newline
    if not content.endswith('\n'):
        content += '\n'
    
    # Fix function spacing (ensure 2 blank lines between functions)
    # This is a simplistic approach and might need manual adjustments
    content = re.sub(r'(\n)def ', r'\n\n\ndef ', content)
    content = re.sub(r'\n\n\n\n+def ', r'\n\n\ndef ', content)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed {file_path}")

def main():
    """Find and fix Python files with linting issues."""
    directories = ['src', 'tests']
    for directory in directories:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    fix_file(file_path)

if __name__ == "__main__":
    main()